#!/usr/bin/env python3
"""Скрипт для проверки конфигурации каналов в Redis."""
import asyncio
import sys
sys.path.insert(0, '/Users/maximkataev/Desktop/rate_posts_bot')

from src.services.redis_service import redis_service


async def main():
    """Check configured channels."""
    print("🔍 Проверка конфигурации каналов...\n")
    
    # Connect to Redis
    await redis_service.connect()
    
    try:
        # Get all channels
        channels = await redis_service.get_all_channels()
        
        if not channels:
            print("❌ Нет настроенных каналов")
            print("\nДобавьте канал через бота: /add_channel <channel_id>")
            return
        
        print(f"✅ Найдено каналов: {len(channels)}\n")
        
        # Check each channel
        for channel_id in channels:
            config = await redis_service.get_channel_config(channel_id)
            
            print(f"📌 Канал ID: {channel_id}")
            if config:
                print(f"   Включен: {'✅ Да' if config.get('enabled') else '❌ Нет'}")
                print(f"   Кастомный промпт: {'✅ Да' if config.get('custom_prompt') else '❌ Нет'}")
                print(f"   Дата добавления: {config.get('added_at', 'Не указана')}")
            else:
                print("   ⚠️  Конфигурация не найдена")
            print()
        
    finally:
        await redis_service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
