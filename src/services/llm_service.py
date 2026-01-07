"""LLM service for post evaluation using multiple providers."""
import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai

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
        
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key)
        
        # HTTP client for other APIs
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        """Close HTTP clients."""
        await self.http_client.aclose()
    
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
        image_url: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate post using OpenAI GPT."""
        try:
            prompt = self._format_prompt(content, "openai", custom_prompt)
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Add image if provided
            if image_url:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
            
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content
            score, comment = self._parse_evaluation(result_text)
            
            return EvaluationResult(
                model_name="OpenAI GPT",
                score=score,
                comment=comment,
                success=True
            )
        except Exception as e:
            logger.error(f"OpenAI evaluation failed: {e}")
            return EvaluationResult(
                model_name="OpenAI GPT",
                score=None,
                comment="",
                success=False,
                error=str(e)
            )
    
    async def evaluate_with_claude(
        self,
        content: str,
        image_url: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate post using Anthropic Claude."""
        try:
            prompt = self._format_prompt(content, "claude", custom_prompt)
            
            # Build message content
            message_content = [{"type": "text", "text": prompt}]
            
            # Add image if provided (Claude needs base64 or URL)
            if image_url:
                # For simplicity, we'll include URL in text
                # In production, fetch and convert to base64
                message_content[0]["text"] += f"\n\nИзображение: {image_url}"
            
            message = await self.anthropic_client.messages.create(
                model=settings.anthropic_model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": message_content}
                ]
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
        image_url: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate post using Google Gemini."""
        try:
            prompt = self._format_prompt(content, "gemini", custom_prompt)
            
            model = genai.GenerativeModel(settings.gemini_model)
            
            # Prepare content
            content_parts = [prompt]
            if image_url:
                content_parts.append(f"\n\nИзображение: {image_url}")
            
            response = await asyncio.to_thread(
                model.generate_content,
                content_parts
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
    
    async def evaluate_post(
        self,
        content: str,
        image_url: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> List[EvaluationResult]:
        """
        Evaluate post with multiple LLMs in parallel.
        
        Args:
            content: Post text content
            image_url: Optional image URL
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
        
        if models:
            evaluators = [
                available_models[model] 
                for model in models 
                if model in available_models
            ]
        else:
            evaluators = list(available_models.values())
        
        # Run evaluations in parallel
        tasks = []
        
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
            return "❌ Не удалось получить оценки от моделей"
        
        successful_results = [r for r in results if r.success and r.score]
        
        if not successful_results:
            return "❌ Все модели не смогли оценить пост"
        
        # Calculate average score
        avg_score = sum(r.score for r in successful_results) / len(successful_results)
        
        # Build response
        lines = [
            f"📊 Оценка поста ({len(successful_results)} моделей):",
            f"",
            f"🎯 Средняя оценка: {avg_score:.1f}/10",
            f""
        ]
        
        # Add individual evaluations
        for result in successful_results:
            emoji = "🟢" if result.score >= 8 else "🟡" if result.score >= 6 else "🔴"
            lines.append(f"{emoji} {result.model_name}: {result.score}/10")
            if result.comment and len(result.comment) < 200:
                lines.append(f"   💬 {result.comment}")
            lines.append("")
        
        # Add failed models info
        failed_results = [r for r in results if not r.success]
        if failed_results:
            lines.append(f"⚠️ Не ответили: {', '.join(r.model_name for r in failed_results)}")
        
        return "\n".join(lines)


# Global instance
llm_service = LLMService()
