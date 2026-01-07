#!/bin/bash

# Скрипт быстрого запуска бота с Doppler

echo "🚀 Запуск Telegram Post Evaluator Bot..."
echo ""

# Проверка установки Doppler
if ! command -v doppler &> /dev/null; then
    echo "❌ Doppler не установлен. Установите его:"
    echo "   brew install dopplerhq/cli/doppler"
    exit 1
fi

# Проверка Redis через Docker Compose
echo "📦 Проверка Redis..."
if ! docker-compose ps redis | grep -q "Up"; then
    echo "▶️  Запуск Redis через Docker Compose..."
    docker-compose up -d redis
    echo "⏳ Ожидание запуска Redis..."
    sleep 3
fi

# Проверка подключения к Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis работает"
else
    echo "❌ Redis не отвечает. Проверьте docker-compose."
    exit 1
fi

echo ""
echo "🤖 Запуск бота..."
echo "   Для остановки нажмите Ctrl+C"
echo ""

# Активация виртуального окружения и запуск через Doppler
source venv/bin/activate
doppler run --project rate-posts-bot --config dev -- python main.py
