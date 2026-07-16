"""Channel handlers for processing new posts."""
import logging
import base64
import io
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from PIL import Image

from src.services.redis_service import redis_service
from src.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = Router()


async def download_and_encode_image(bot, file_id: str) -> Optional[dict]:
    """
    Download image from Telegram and encode to base64.

    Returns:
        Dict with base64 data and media type, or None if failed
    """
    try:
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)

        # Read bytes
        image_data = file_bytes.read()

        # Encode to base64
        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

        # Determine media type from file extension
        file_ext = file.file_path.split('.')[-1].lower()
        media_type = f"image/{file_ext if file_ext in ['jpeg', 'jpg', 'png', 'gif', 'webp'] else 'jpeg'}"

        logger.info(f"Downloaded and encoded image: {file_id} ({len(image_data)} bytes)")

        return {
            "base64": image_base64,
            "media_type": media_type
        }
    except Exception as e:
        logger.error(f"Failed to download image {file_id}: {e}")
        return None


async def extract_video_frames(bot, video_file_id: str, num_frames: int = 3) -> list[dict]:
    """
    Extract frames from video and encode to base64.

    Args:
        bot: Bot instance
        video_file_id: Telegram video file_id
        num_frames: Number of frames to extract (default: 3 - start, middle, end)

    Returns:
        List of dicts with base64 encoded frames
    """
    frames = []
    try:
        # Download video
        file = await bot.get_file(video_file_id)
        video_bytes = await bot.download_file(file.file_path)

        # For now, we'll use the video thumbnail if available
        # Full video frame extraction would require ffmpeg
        # This is a simplified version - in production use ffmpeg or similar
        logger.info(f"Video processing requested for {video_file_id} - using thumbnail")

        # Try to get video thumbnail
        # Note: Telegram provides thumbnails for videos
        # For full frame extraction, you'd need ffmpeg integration

    except Exception as e:
        logger.error(f"Failed to extract video frames {video_file_id}: {e}")

    return frames


async def extract_post_content(message: Message, bot) -> tuple[Optional[str], Optional[list]]:
    """
    Extract text and media from message.

    Args:
        message: Telegram message
        bot: Bot instance for downloading files

    Returns:
        Tuple of (text_content, media_data)
        media_data is a list of dicts with base64 encoded images/video frames
    """
    text = message.text or message.caption or ""
    media_data = []

    # Check for photos
    if message.photo:
        photo = message.photo[-1]  # Highest resolution
        image_dict = await download_and_encode_image(bot, photo.file_id)
        if image_dict:
            media_data.append(image_dict)

    # Check for video
    if message.video:
        # For videos, extract thumbnail first
        if message.video.thumbnail:
            thumb_dict = await download_and_encode_image(bot, message.video.thumbnail.file_id)
            if thumb_dict:
                media_data.append(thumb_dict)
                logger.info(f"Using video thumbnail for {message.video.file_id}")
        else:
            logger.info(f"Video {message.video.file_id} has no thumbnail, skipping visual analysis")

    return text, media_data if media_data else None


async def should_process_message(message: Message) -> bool:
    """
    Check if message should be processed.

    Returns:
        True if message should be evaluated
    """
    # Only process channel posts
    if not message.chat.type == "channel":
        logger.debug(f"Skipping non-channel message (type: {message.chat.type})")
        return False

    # Check if channel is monitored
    is_monitored = await redis_service.is_channel_monitored(message.chat.id)
    if not is_monitored:
        logger.info(
            f"Ignoring post from non-monitored channel {message.chat.id} "
            f"(title: {message.chat.title})"
        )
        return False

    # Check if channel is enabled
    config = await redis_service.get_channel_config(message.chat.id)
    if not config or not config.get("enabled", True):
        logger.info(f"Channel {message.chat.id} is disabled")
        return False

    # Only process specific content types
    if message.poll:
        # Process polls
        logger.debug(f"Processing poll from channel {message.chat.id}")
        return True

    if message.text or message.caption or message.photo or message.video:
        # Process text posts (with or without images/videos)
        logger.debug(
            f"Processing post from channel {message.chat.id}: "
            f"text={bool(message.text or message.caption)}, "
            f"photo={bool(message.photo)}, video={bool(message.video)}"
        )
        return True

    # Ignore other types (audio, documents, stickers, etc.)
    logger.debug(
        f"Ignoring unsupported content type in channel {message.chat.id}: "
        f"{message.content_type}"
    )
    return False


@router.channel_post()
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
            media_data = None
        else:
            # Handle text/image/video post
            content, media_data = await extract_post_content(message, message.bot)

        if not content and not media_data:
            logger.warning("Empty content and no media, skipping")
            return

        # Evaluate post with multiple LLMs
        try:
            results = await llm_service.evaluate_post(
                content=content or "Пост без текста, только медиа",
                media_data=media_data,
                custom_prompt=custom_prompt
            )

            # Format and send evaluation
            evaluation_text = llm_service.format_evaluation_response(results)

            # Send final result
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
            await message.reply(
                "❌ Произошла ошибка при оценке поста"
            )
    
    except Exception as e:
        logger.error(f"Error handling channel post: {e}")


@router.channel_post(F.content_type.in_({
    "video", "audio", "document", "sticker", "animation",
    "voice", "video_note"
}))
async def handle_unsupported_content(message: Message):
    """Handle unsupported content types - just log and ignore."""
    logger.debug(
        f"Ignoring unsupported content type {message.content_type} "
        f"in channel {message.chat.id}"
    )
