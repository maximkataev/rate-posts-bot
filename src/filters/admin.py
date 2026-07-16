"""Admin access filter."""
from aiogram.filters import BaseFilter
from aiogram.types import Message

from config.settings import settings


class IsAdmin(BaseFilter):
    """Filter to check if user is admin."""

    async def __call__(self, message: Message) -> bool:
        """Check if message is from admin user."""
        return message.from_user.id == settings.telegram_admin_id
