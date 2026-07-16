"""Channel handlers for processing new posts."""
import logging
import base64
import io
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from PIL import Image

from config.settings import settings
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


def get_origin_channel_id(message: Message) -> Optional[int]:
    """
    Get source channel id from an automatic forward in the discussion group.

    Returns:
        Channel id or None if message is not an auto-forward from a channel
    """
    origin = message.forward_origin
    chat = getattr(origin, "chat", None)
    return chat.id if chat else None


async def should_process_forward(message: Message) -> bool:
    """
    Check if auto-forwarded channel post should be evaluated.

    Returns:
        True if message should be evaluated
    """
    channel_id = get_origin_channel_id(message)
    if channel_id is None:
        logger.debug("Auto-forward without channel origin, skipping")
        return False

    # Only the configured channel is monitored
    if channel_id != settings.telegram_channel_id:
        logger.info(f"Ignoring post from non-monitored channel {channel_id}")
        return False

    # Only process specific content types
    if message.poll:
        # Process polls
        logger.debug(f"Processing poll from channel {channel_id}")
        return True

    if message.text or message.caption or message.photo or message.video:
        # Process text posts (with or without images/videos)
        logger.debug(
            f"Processing post from channel {channel_id}: "
            f"text={bool(message.text or message.caption)}, "
            f"photo={bool(message.photo)}, video={bool(message.video)}"
        )
        return True

    # Ignore other types (audio, documents, stickers, etc.)
    logger.debug(
        f"Ignoring unsupported content type from channel {channel_id}: "
        f"{message.content_type}"
    )
    return False


# Пост канала прилетает в привязанную группу обсуждений автофорвардом;
# реплай на него публикуется как комментарий под постом.
# Для этого бот должен состоять в группе обсуждений (лучше админом).
@router.message(F.is_automatic_forward == True)
async def handle_channel_post(message: Message):
    """Evaluate channel post and reply in comments (discussion group)."""
    try:
        # Check if we should process this message
        if not await should_process_forward(message):
            return

        channel_id = get_origin_channel_id(message)
        logger.info(
            f"Processing post from channel {channel_id} "
            f"(discussion message_id: {message.message_id})"
        )

        # Extract content (the auto-forward carries the same text/media as the post)
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
                media_data=media_data
            )

            # Format and send evaluation
            evaluation_text = llm_service.format_evaluation_response(results)

            # Reply to the auto-forward = comment under the channel post
            await message.reply(
                evaluation_text,
                parse_mode=ParseMode.HTML
            )

            logger.info(
                f"Successfully evaluated post from channel {channel_id} "
                f"(comment in chat {message.chat.id})"
            )

        except Exception as e:
            logger.error(f"Error evaluating post: {e}")
            await message.reply(
                "❌ Произошла ошибка при оценке поста"
            )

    except Exception as e:
        logger.error(f"Error handling channel post: {e}")
