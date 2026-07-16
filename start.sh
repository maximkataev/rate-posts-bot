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

# Определение команды docker compose (новая версия использует "docker compose" без дефиса)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose не установлен."
    echo "   Установите Docker Desktop: https://www.docker.com/products/docker-desktop"
    echo ""
    echo "   Или запустите Redis вручную:"
    echo "   brew install redis && brew services start redis"
    exit 1
fi

# Проверка Redis через Docker Compose
echo "📦 Проверка Redis..."
if ! $DOCKER_COMPOSE ps redis 2>/dev/null | grep -q "Up"; then
    echo "▶️  Запуск Redis через Docker Compose..."
    $DOCKER_COMPOSE up -d redis
    echo "⏳ Ожидание запуска Redis..."
    sleep 3
fi

# Проверка подключения к Redis
if $DOCKER_COMPOSE exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis работает"
else
    echo "❌ Redis не отвечает."
    echo "   Попробуйте: $DOCKER_COMPOSE restart redis"
    exit 1
fi

echo ""
echo "🤖 Запуск бота..."
echo "   Для остановки нажмите Ctrl+C"
echo ""

# Активация виртуального окружения и запуск через Doppler
source venv/bin/activate
doppler run --project rate-posts-bot --config dev -- python main.py
