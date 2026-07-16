"""LLM service for post evaluation using multiple providers."""
import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from google import genai
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    stop_after_attempt,
    wait_fixed,
)

from config.settings import settings
from config.prompts import get_prompt

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of post evaluation by an LLM."""
    model_name: str
    score: Optional[int]
    comment: str
    success: bool
    error: Optional[str] = None


class LLMService:
    """Service for evaluating posts with multiple LLMs."""
    
    def __init__(self):
        """Initialize LLM clients."""
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        # Initialize Gemini client with new API
        self.gemini_client = genai.Client(api_key=settings.google_api_key)

        # DeepSeek exposes an OpenAI-compatible API
        self.deepseek_client = (
            AsyncOpenAI(
                api_key=settings.deepseek_api_key,
                base_url="https://api.deepseek.com",
            )
            if settings.deepseek_api_key
            else None
        )

        # HTTP client for other APIs
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        """Close HTTP clients."""
        await self.http_client.aclose()

    async def _call_with_retries(self, make_request):
        """
        Выполняет запрос к LLM с ретраями: до 5 попыток
        с паузой 1 секунда между ними.

        Args:
            make_request: колбэк без аргументов, возвращающий awaitable запроса

        Returns:
            Ответ API после первой успешной попытки
        """
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(5),
            wait=wait_fixed(1),
            reraise=True,
            before_sleep=before_sleep_log(logger, logging.WARNING),
        ):
            with attempt:
                return await make_request()
    
    def _format_prompt(self, content: str, llm_name: str, custom_prompt: Optional[str] = None) -> str:
        """
        Format evaluation prompt for specific LLM.

        Args:
            content: Post content to evaluate
            llm_name: Name of the LLM (openai, claude, gemini)
            custom_prompt: Optional custom prompt template

        Returns:
            Formatted prompt
        """
        template = custom_prompt or get_prompt(llm_name)
        return template.format(content=content)
    
    def _parse_evaluation(self, response: str) -> Tuple[Optional[int], str]:
        """
        Parse LLM response to extract score and comment.
        
        Expected format: "Оценка: X/10. Комментарий."
        
        Returns:
            Tuple of (score, comment)
        """
        try:
            # Try to find score in format "X/10" or just "X"
            lines = response.strip().split('\n')
            score = None
            comment = response
            
            for line in lines:
                if 'оценка:' in line.lower() or 'score:' in line.lower():
                    # Extract number
                    import re
                    match = re.search(r'(\d+)(?:/10)?', line)
                    if match:
                        score = int(match.group(1))
                        score = min(max(score, 1), 10)  # Clamp to 1-10
                        break
            
            return score, response
        except Exception as e:
            logger.warning(f"Failed to parse evaluation: {e}")
            return None, response
    
    async def evaluate_with_openai(
        self,
        content: str,
        media_data: Optional[List[dict]] = None,
        custom_prompt: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate post using OpenAI GPT with optional images."""
        try:
            prompt = self._format_prompt(content, "openai", custom_prompt)

            message_content = [{"type": "text", "text": prompt}]

            # Add images if provided (base64 format)
            if media_data:
                for media in media_data:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media['media_type']};base64,{media['base64']}"
                        }
                    })
                logger.info(f"OpenAI: Added {len(media_data)} images to request")

            messages = [{"role": "user", "content": message_content}]

            response = await self._call_with_retries(
                lambda: self.openai_client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    # gpt-5.x не принимает max_tokens/temperature —
                    # только max_completion_tokens и дефолтную температуру
                    max_completion_tokens=600
                )
            )

            result_text = response.choices[0].message.content
            score, comment = self._parse_evaluation(result_text)

            return EvaluationResult(
                model_name="OpenAI ChatGPT",
                score=score,
                comment=comment,
                success=True
            )
        except Exception as e:
            logger.error(f"OpenAI evaluation failed: {e}")
            return EvaluationResult(
                model_name="OpenAI ChatGPT",
                score=None,
                comment="",
                success=False,
                error=str(e)
            )
    
    async def evaluate_with_claude(
        self,
        content: str,
        media_data: Optional[List[dict]] = None,
        custom_prompt: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate post using Anthropic Claude with optional images."""
        try:
            prompt = self._format_prompt(content, "claude", custom_prompt)

            # Build message content - images first, then text
            message_content = []

            # Add images if provided (Claude requires base64)
            if media_data:
                for media in media_data:
                    message_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media["media_type"],
                            "data": media["base64"],
                        }
                    })
                logger.info(f"Claude: Added {len(media_data)} images to request")

            # Add text prompt
            message_content.append({"type": "text", "text": prompt})

            message = await self._call_with_retries(
                lambda: self.anthropic_client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=500,
                    # claude-sonnet-5 по умолчанию включает adaptive thinking,
                    # которое съедает max_tokens — для короткой оценки отключаем
                    thinking={"type": "disabled"},
                    messages=[
                        {"role": "user", "content": message_content}
                    ]
                )
            )

            result_text = message.content[0].text
            score, comment = self._parse_evaluation(result_text)

            return EvaluationResult(
                model_name="Claude",
                score=score,
                comment=comment,
                success=True
            )
        except Exception as e:
            logger.error(f"Claude evaluation failed: {e}")
            return EvaluationResult(
                model_name="Claude",
                score=None,
                comment="",
                success=False,
                error=str(e)
            )
    
    async def evaluate_with_gemini(
        self,
        content: str,
        media_data: Optional[List[dict]] = None,
        custom_prompt: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate post using Google Gemini with optional images."""
        try:
            prompt = self._format_prompt(content, "gemini", custom_prompt)

            # Prepare content parts
            parts = [prompt]

            # Add images if provided
            if media_data:
                import base64
                import io
                from PIL import Image

                for media in media_data:
                    # Decode base64 to bytes
                    image_bytes = base64.b64decode(media["base64"])
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(image_bytes))
                    parts.append(image)

                logger.info(f"Gemini: Added {len(media_data)} images to request")

            # Use new API - generate_content is sync, run in thread
            response = await self._call_with_retries(
                lambda: asyncio.to_thread(
                    self.gemini_client.models.generate_content,
                    model=settings.gemini_model,
                    contents=parts
                )
            )

            result_text = response.text
            score, comment = self._parse_evaluation(result_text)

            return EvaluationResult(
                model_name="Gemini",
                score=score,
                comment=comment,
                success=True
            )
        except Exception as e:
            logger.error(f"Gemini evaluation failed: {e}")
            return EvaluationResult(
                model_name="Gemini",
                score=None,
                comment="",
                success=False,
                error=str(e)
            )
    
    async def evaluate_with_deepseek(
        self,
        content: str,
        media_data: Optional[List[dict]] = None,
        custom_prompt: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate post using DeepSeek (text only — model has no vision support)."""
        try:
            if not self.deepseek_client:
                return EvaluationResult(
                    model_name="DeepSeek",
                    score=None,
                    comment="",
                    success=False,
                    error="DEEPSEEK_API_KEY is not configured"
                )

            prompt = self._format_prompt(content, "deepseek", custom_prompt)

            if media_data:
                logger.info(
                    f"DeepSeek: skipping {len(media_data)} images (no vision support)"
                )

            response = await self._call_with_retries(
                lambda: self.deepseek_client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7
                )
            )

            result_text = response.choices[0].message.content
            score, comment = self._parse_evaluation(result_text)

            return EvaluationResult(
                model_name="DeepSeek",
                score=score,
                comment=comment,
                success=True
            )
        except Exception as e:
            logger.error(f"DeepSeek evaluation failed: {e}")
            return EvaluationResult(
                model_name="DeepSeek",
                score=None,
                comment="",
                success=False,
                error=str(e)
            )

    async def evaluate_post(
        self,
        content: str,
        media_data: Optional[List[dict]] = None,
        custom_prompt: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> List[EvaluationResult]:
        """
        Evaluate post with multiple LLMs in parallel.

        Args:
            content: Post text content
            media_data: Optional list of media (images/videos) as base64
            custom_prompt: Optional custom evaluation prompt
            models: List of models to use (default: all available)

        Returns:
            List of evaluation results
        """
        # Determine which models to use
        available_models = {
            "openai": self.evaluate_with_openai,
            "claude": self.evaluate_with_claude,
            "gemini": self.evaluate_with_gemini,
        }
        if self.deepseek_client:
            available_models["deepseek"] = self.evaluate_with_deepseek

        if models:
            evaluators = [
                available_models[model]
                for model in models
                if model in available_models
            ]
        else:
            evaluators = list(available_models.values())

        logger.info(
            f"Starting evaluation with {len(evaluators)} models"
            f"{f' and {len(media_data)} media files' if media_data else ''}"
        )

        # Run evaluations in parallel
        tasks = [
            evaluator(content, media_data, custom_prompt)
            for evaluator in evaluators
        ]

        logger.debug(f"Created {len(tasks)} evaluation tasks")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        evaluation_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Evaluation failed with exception: {result}")
            elif isinstance(result, EvaluationResult):
                evaluation_results.append(result)

        return evaluation_results
    
    def format_evaluation_response(
        self,
        results: List[EvaluationResult]
    ) -> str:
        """
        Format evaluation results into a readable message.

        Args:
            results: List of evaluation results

        Returns:
            Formatted message text
        """
        if not results:
            logger.error("No evaluation results received from any model")
            return "❌ Не удалось получить оценки от моделей"

        # Log all results for debugging
        logger.info(f"Received {len(results)} evaluation results")
        for result in results:
            if result.success:
                logger.info(
                    f"  ✓ {result.model_name}: score={result.score}, "
                    f"comment_length={len(result.comment) if result.comment else 0}"
                )
            else:
                logger.warning(
                    f"  ✗ {result.model_name} failed: {result.error}"
                )

        successful_results = [r for r in results if r.success and r.score]

        if not successful_results:
            failed_models = [r.model_name for r in results if not r.success]
            logger.error(
                f"All models failed to evaluate. Failed models: {failed_models}"
            )
            # Show which models failed and why
            error_details = []
            for r in results:
                if not r.success:
                    error_details.append(f"{r.model_name}: {r.error}")
            logger.error(f"Error details: {'; '.join(error_details)}")
            return "❌ Все модели не смогли оценить пост"
        
        # Calculate average score
        avg_score = sum(r.score for r in successful_results) / len(successful_results)
        
        # Build response
        lines = [
            f"📊 Оценка поста ({len(successful_results)} моделей):",
            f""
        ]
        
        # Add individual evaluations
        for result in successful_results:
            lines.append(f"{result.model_name}")
            if result.comment:
                # Длинные ответы обрезаем, а не прячем —
                # иначе модель остаётся в списке без текста
                comment = result.comment.strip()
                if len(comment) > 350:
                    comment = comment[:350].rstrip() + "…"
                lines.append(f"💬 {comment}")
            lines.append("")
        
        # Add failed models info
        failed_results = [r for r in results if not r.success]
        if failed_results:
            lines.append(f"⚠️ Не ответили: {', '.join(r.model_name for r in failed_results)}")
        
        return "\n".join(lines)


# Global instance
llm_service = LLMService()
