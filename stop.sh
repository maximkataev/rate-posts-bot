#!/bin/bash

# Скрипт остановки сервисов

echo "🛑 Остановка сервисов..."

# Остановка Redis
echo "📦 Остановка Redis..."
docker-compose down

echo "✅ Все сервисы остановлены"
