"""Admin handlers for bot management."""
import logging
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "👋 Привет! Я бот для оценки постов в канале.\n\n"
        "Слежу за настроенным каналом и пишу рецензии четырёх AI-моделей "
        "в комментарии к каждому посту.\n\n"
        "/help - Справка"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = """
📚 <b>Как я работаю</b>

Канал задан в конфиге бота. Когда в нём выходит пост, я оцениваю его несколькими AI-моделями и публикую рецензии комментарием к посту.

<b>Что нужно для работы:</b>
1. Я добавлен администратором в канал
2. К каналу привязана группа обсуждений
3. Я добавлен в эту группу (лучше админом)

<b>Что оцениваю:</b>
• Текстовые посты
• Посты с изображениями
• Опросы

<b>Что игнорирую:</b>
• Видео (смотрю только превью)
• Аудио, документы, стикеры

<b>Модели для оценки:</b>
• OpenAI GPT
• Anthropic Claude
• Google Gemini
• DeepSeek

По всем вопросам пиши @maksimkin
"""
    await message.answer(help_text, parse_mode=ParseMode.HTML)
