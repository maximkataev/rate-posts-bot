"""Channel handlers for processing new posts."""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode

from src.services.redis_service import redis_service
from src.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = Router()


def extract_post_content(message: Message) -> tuple[Optional[str], Optional[str]]:
    """
    Extract text and image URL from message.
    
    Returns:
        Tuple of (text_content, image_url)
    """
    text = message.text or message.caption or ""
    image_url = None
    
    # Check for photos
    if message.photo:
        # Get highest resolution photo
        photo = message.photo[-1]
        # In production, you'd want to download and upload to a CDN
        # For now, we'll use file_id (models need actual URLs)
        # image_url = f"telegram://photo/{photo.file_id}"
        # Since we can't easily get direct URLs, we'll skip images for now
        # Or you could download and upload to your CDN
        logger.info(f"Post has photo with file_id: {photo.file_id}")
    
    return text, image_url


async def should_process_message(message: Message) -> bool:
    """
    Check if message should be processed.
    
    Returns:
        True if message should be evaluated
    """
    # Only process channel posts
    if not message.chat.type == "channel":
        return False
    
    # Check if channel is monitored
    is_monitored = await redis_service.is_channel_monitored(message.chat.id)
    if not is_monitored:
        return False
    
    # Check if channel is enabled
    config = await redis_service.get_channel_config(message.chat.id)
    if not config or not config.get("enabled", True):
        return False
    
    # Only process specific content types
    if message.poll:
        # Process polls
        return True
    
    if message.text or message.caption:
        # Process text posts (with or without images)
        return True
    
    # Ignore other types (video, audio, documents, stickers, etc.)
    return False


@router.message(F.chat.type == "channel")
async def handle_channel_post(message: Message):
    """Handle new posts in monitored channels."""
    try:
        # Check if we should process this message
        if not await should_process_message(message):
            return
        
        logger.info(
            f"Processing post from channel {message.chat.id} "
            f"(message_id: {message.message_id})"
        )
        
        # Get channel config for custom prompt
        config = await redis_service.get_channel_config(message.chat.id)
        custom_prompt = config.get("custom_prompt") if config else None
        
        # Extract content
        if message.poll:
            # Handle poll
            poll = message.poll
            content = (
                f"Опрос: {poll.question}\n"
                f"Варианты:\n" + 
                "\n".join(f"- {opt.text}" for opt in poll.options)
            )
            image_url = None
        else:
            # Handle text/image post
            content, image_url = extract_post_content(message)
        
        if not content:
            logger.warning("Empty content, skipping")
            return
        
        # Send "processing" message
        processing_msg = await message.reply(
            "⏳ Оцениваю пост с помощью AI моделей...",
            parse_mode=ParseMode.HTML
        )
        
        # Evaluate post with multiple LLMs
        try:
            results = await llm_service.evaluate_post(
                content=content,
                image_url=image_url,
                custom_prompt=custom_prompt
            )
            
            # Format and send evaluation
            evaluation_text = llm_service.format_evaluation_response(results)
            
            # Delete processing message and send final result
            await processing_msg.delete()
            await message.reply(
                evaluation_text,
                parse_mode=ParseMode.HTML
            )
            
            logger.info(
                f"Successfully evaluated post {message.message_id} "
                f"in channel {message.chat.id}"
            )
            
        except Exception as e:
            logger.error(f"Error evaluating post: {e}")
            await processing_msg.edit_text(
                "❌ Произошла ошибка при оценке поста"
            )
    
    except Exception as e:
        logger.error(f"Error handling channel post: {e}")


@router.message(F.chat.type == "channel", F.content_type.in_({
    "video", "audio", "document", "sticker", "animation", 
    "voice", "video_note"
}))
async def handle_unsupported_content(message: Message):
    """Handle unsupported content types - just log and ignore."""
    logger.debug(
        f"Ignoring unsupported content type {message.content_type} "
        f"in channel {message.chat.id}"
    )
