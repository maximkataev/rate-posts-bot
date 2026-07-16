"""Admin handlers for bot management."""
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode

from src.services.redis_service import redis_service
from src.filters import IsAdmin

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "👋 Привет! Я бот для оценки постов в каналах.\n\n"
        "Добавь меня администратором в свой канал с правами на публикацию сообщений, "
        "и я буду оценивать новые посты с помощью нескольких AI моделей.\n\n"
        "Команды:\n"
        "/add_channel &lt;channel_id&gt; - Добавить канал для мониторинга\n"
        "/remove_channel &lt;channel_id&gt; - Удалить канал\n"
        "/list_channels - Список отслеживаемых каналов\n"
        "/help - Справка"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = """
📚 <b>Справка по использованию</b>

<b>Основные команды:</b>
/add_channel &lt;channel_id&gt; - Добавить канал для мониторинга
/remove_channel &lt;channel_id&gt; - Удалить канал
/list_channels - Список отслеживаемых каналов

<b>Как получить ID канала:</b>
1. Перешли любое сообщение из канала боту @userinfobot
2. Скопируй "Forwarded from chat" ID (число с минусом, например: -1001234567890)
3. Используй этот ID в команде /add_channel

<b>Настройка канала:</b>
Бот должен быть добавлен в канал как администратор с правами:
• Публикация сообщений (для отправки оценок)

<b>Что оценивает бот:</b>
• Текстовые посты
• Посты с изображениями
• Посты с текстом и изображениями
• Опросы

<b>Что игнорируется:</b>
• Видео
• Аудио
• Документы
• Стикеры

<b>Модели для оценки:</b>
• OpenAI GPT-4
• Anthropic Claude
• Google Gemini

По всем вопросам пиши @maksimkin
"""
    await message.answer(help_text, parse_mode=ParseMode.HTML)


@router.message(Command("add_channel"), IsAdmin())
async def cmd_add_channel(message: Message):
    """Handle /add_channel command."""
    try:
        # Parse command arguments
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.answer(
                "❌ Укажи ID канала\n"
                "Пример: /add_channel -1001234567890\n\n"
                "Как получить ID канала:\n"
                "1. Перешли сообщение из канала боту @userinfobot\n"
                "2. Скопируй 'Forwarded from chat' ID"
            )
            return
        
        channel_id = int(args[1])
        
        # Check if bot is admin in channel
        try:
            chat = await message.bot.get_chat(channel_id)
            bot_member = await message.bot.get_chat_member(channel_id, message.bot.id)
            
            if bot_member.status not in ["administrator", "creator"]:
                await message.answer(
                    f"❌ Я не являюсь администратором канала {chat.title}\n"
                    "Добавь меня как администратора с правами на публикацию сообщений"
                )
                return
            
            # Check posting permissions
            if not bot_member.can_post_messages:
                await message.answer(
                    f"⚠️ У меня нет прав на публикацию в канале {chat.title}\n"
                    "Дай мне права на публикацию сообщений"
                )
                return
            
        except Exception as e:
            await message.answer(
                f"❌ Не могу получить доступ к каналу\n"
                f"Убедись, что ID правильный и я добавлен как администратор\n"
                f"Ошибка: {e}"
            )
            return
        
        # Add channel to Redis
        success = await redis_service.add_channel(channel_id)
        
        if success:
            await message.answer(
                f"✅ Канал <b>{chat.title}</b> добавлен!\n"
                f"ID: <code>{channel_id}</code>\n\n"
                "Теперь я буду оценивать новые посты в этом канале",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"User {message.from_user.id} added channel {channel_id}")
        else:
            await message.answer("❌ Не удалось добавить канал. Попробуй позже")
            
    except ValueError:
        await message.answer(
            "❌ Неверный формат ID канала\n"
            "ID должен быть числом, например: -1001234567890"
        )
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


@router.message(Command("remove_channel"), IsAdmin())
async def cmd_remove_channel(message: Message):
    """Handle /remove_channel command."""
    try:
        # Parse command arguments
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.answer(
                "❌ Укажи ID канала\n"
                "Пример: /remove_channel -1001234567890"
            )
            return
        
        channel_id = int(args[1])
        
        # Check if channel exists
        is_monitored = await redis_service.is_channel_monitored(channel_id)
        
        if not is_monitored:
            await message.answer("❌ Этот канал не отслеживается")
            return
        
        # Remove channel
        success = await redis_service.remove_channel(channel_id)
        
        if success:
            await message.answer(
                f"✅ Канал удалён\n"
                f"ID: <code>{channel_id}</code>",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"User {message.from_user.id} removed channel {channel_id}")
        else:
            await message.answer("❌ Не удалось удалить канал. Попробуй позже")
            
    except ValueError:
        await message.answer(
            "❌ Неверный формат ID канала\n"
            "ID должен быть числом"
        )
    except Exception as e:
        logger.error(f"Error removing channel: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


@router.message(Command("list_channels"), IsAdmin())
async def cmd_list_channels(message: Message):
    """Handle /list_channels command."""
    try:
        channels = await redis_service.get_all_channels()
        
        if not channels:
            await message.answer("📭 Нет отслеживаемых каналов")
            return
        
        # Get channel info
        channel_info = []
        for channel_id in channels:
            try:
                chat = await message.bot.get_chat(channel_id)
                config = await redis_service.get_channel_config(channel_id)
                
                status = "🟢 Активен" if config.get("enabled") else "🔴 Отключён"
                channel_info.append(
                    f"• <b>{chat.title}</b>\n"
                    f"  ID: <code>{channel_id}</code>\n"
                    f"  Статус: {status}"
                )
            except Exception as e:
                channel_info.append(
                    f"• ID: <code>{channel_id}</code>\n"
                    f"  ⚠️ Не удалось получить информацию"
                )
        
        response = "📋 <b>Отслеживаемые каналы:</b>\n\n" + "\n\n".join(channel_info)
        await message.answer(response, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


# Fallback-хендлеры для не-админов: регистрируются ПОСЛЕ IsAdmin-хендлеров,
# иначе aiogram отдаёт команду первому совпавшему и админ тоже получает отказ.

@router.message(Command("add_channel"))
async def cmd_add_channel_unauthorized(message: Message):
    """Handle /add_channel from unauthorized users."""
    await message.answer(
        "❌ У вас нет прав для использования этой команды.\n"
        "Этот бот доступен только для администратора."
    )


@router.message(Command("remove_channel"))
async def cmd_remove_channel_unauthorized(message: Message):
    """Handle /remove_channel from unauthorized users."""
    await message.answer(
        "❌ У вас нет прав для использования этой команды.\n"
        "Этот бот доступен только для администратора."
    )


@router.message(Command("list_channels"))
async def cmd_list_channels_unauthorized(message: Message):
    """Handle /list_channels from unauthorized users."""
    await message.answer(
        "❌ У вас нет прав для использования этой команды.\n"
        "Этот бот доступен только для администратора."
    )
