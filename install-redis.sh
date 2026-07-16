#!/bin/bash

# Быстрая установка Redis через Homebrew

echo "📦 Установка Redis через Homebrew..."
echo ""

# Проверка Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew не установлен."
    echo "   Установите его: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Установка Redis
echo "▶️  Установка Redis..."
brew install redis

echo ""
echo "▶️  Запуск Redis..."
brew services start redis

echo ""
echo "⏳ Ожидание запуска Redis..."
sleep 2

# Проверка
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis установлен и работает!"
    echo ""
    echo "🚀 Теперь можете запустить бота:"
    echo "   ./start-local.sh"
else
    echo "⚠️  Redis установлен, но не запущен."
    echo "   Попробуйте: brew services restart redis"
fi
