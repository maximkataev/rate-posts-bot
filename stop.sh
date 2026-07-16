#!/bin/bash

# Скрипт остановки сервисов

echo "🛑 Остановка сервисов..."

# Определение команды docker compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose не найден"
    exit 1
fi

# Остановка Redis
echo "📦 Остановка Redis..."
$DOCKER_COMPOSE down

echo "✅ Все сервисы остановлены"
