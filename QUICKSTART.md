# Быстрый запуск

## Предварительные требования

1. **Docker** - для запуска Redis
2. **Doppler CLI** - для управления секретами (уже установлен ✅)
3. **Python 3.11+** с виртуальным окружением

## Запуск за 30 секунд

```bash
# 1. Запустить бота
./start.sh
```

Вот и всё! Скрипт автоматически:
- Проверит Doppler
- Запустит Redis через Docker Compose
- Активирует виртуальное окружение
- Загрузит секреты из Doppler
- Запустит бота

## Остановка

```bash
./stop.sh
```

## Что уже настроено

✅ **Doppler проект**: `rate-posts-bot`
✅ **Конфигурация**: `dev`
✅ **Секреты в Doppler**:
- `TELEGRAM_BOT_TOKEN`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY` (из CHATGPT_API_TOKEN)
- `GEMINI_API_KEY`
- `REDIS_HOST=localhost`
- `REDIS_PORT=6379`
- Все модели и настройки

## Проверка настроек

```bash
# Посмотреть все секреты
doppler secrets --project rate-posts-bot --config dev

# Протестировать загрузку настроек
doppler run --project rate-posts-bot --config dev -- python -c "from config.settings import settings; print('✅ Settings OK')"
```

## Альтернативный запуск (вручную)

```bash
# 1. Запустить Redis
docker-compose up -d redis

# 2. Проверить Redis
docker-compose exec redis redis-cli ping

# 3. Активировать venv
source venv/bin/activate

# 4. Запустить бота
doppler run --project rate-posts-bot --config dev -- python main.py
```

## Настройка промптов

Промпты для каждой LLM теперь в отдельном файле: [config/prompts.py](config/prompts.py)

- **OpenAI**: нейтральный промпт
- **Claude**: критичный рецензент (может занизить оценку)
- **Gemini**: подбадривающий рецензент

Просто отредактируйте файл и перезапустите бота!

## Troubleshooting

### Redis не запускается
```bash
# Проверьте Docker
docker ps

# Перезапустите Redis
docker-compose restart redis
```

### Ошибка Doppler
```bash
# Проверьте настройку проекта
doppler setup --project rate-posts-bot --config dev

# Проверьте секреты
doppler secrets
```

### Бот не видит сообщения в канале
1. Добавьте бота в канал как администратора
2. Дайте права на публикацию сообщений
3. Зарегистрируйте канал: `/add_channel <channel_id>`

## Дополнительная информация

📖 Полная инструкция: [SETUP_GUIDE.md](SETUP_GUIDE.md)
📖 Общая документация: [README.md](README.md)
