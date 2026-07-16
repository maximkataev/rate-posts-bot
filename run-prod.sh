#!/bin/bash

# Прод-запуск бота под launchd: ждём Redis, затем стартуем через Doppler.
# Используется агентом ~/Library/LaunchAgents/com.rate-posts-bot.plist

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")"

# Ждём Redis до 30 секунд (после ребута он может подниматься позже нас)
for i in $(seq 1 30); do
    if redis-cli ping > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis is not available, exiting (launchd will restart us)" >&2
    exit 1
fi

exec doppler run --project rate-posts-bot --config dev -- ./venv/bin/python main.py
