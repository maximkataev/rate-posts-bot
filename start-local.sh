#!/bin/bash

# Скрипт быстрого запуска бота с локальным Redis (через Homebrew)

echo "🚀 Запуск Telegram Post Evaluator Bot (локальная версия)..."
echo ""

# Проверка установки Doppler
if ! command -v doppler &> /dev/null; then
    echo "❌ Doppler не установлен. Установите его:"
    echo "   brew install dopplerhq/cli/doppler"
    exit 1
fi

# Проверка Redis
echo "📦 Проверка Redis..."
if ! command -v redis-cli &> /dev/null; then
    echo "❌ Redis не установлен."
    echo "   Установите его: brew install redis"
    exit 1
fi

# Проверка работы Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "▶️  Запуск Redis через Homebrew..."
    brew services start redis
    echo "⏳ Ожидание запуска Redis..."
    sleep 2
    
    # Повторная проверка
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "❌ Redis не запустился. Попробуйте вручную:"
        echo "   brew services restart redis"
        exit 1
    fi
fi

echo "✅ Redis работает"

echo ""
echo "🤖 Запуск бота..."
echo "   Для остановки нажмите Ctrl+C"
echo ""

# Активация виртуального окружения и запуск через Doppler
source venv/bin/activate
doppler run --project rate-posts-bot --config dev -- python main.py
