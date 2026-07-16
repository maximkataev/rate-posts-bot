# ✅ Проект готов к запуску!

## 🎉 Что было сделано

### 1. Рефакторинг промптов
- ✅ Создан [config/prompts.py](config/prompts.py) с отдельными промптами для каждой LLM
- ✅ **OpenAI**: нейтральный промпт с рекомендацией лайка
- ✅ **Claude**: критичный рецензент (может занизить оценку)
- ✅ **Gemini**: подбадривающий рецензент
- ✅ Обновлен [llm_service.py](src/services/llm_service.py) для использования специфичных промптов

### 2. Настройка Doppler
- ✅ Проект: `rate-posts-bot`
- ✅ Конфигурация: `dev`
- ✅ Все API ключи добавлены и проверены:
  - TELEGRAM_BOT_TOKEN ✓
  - OPENAI_API_KEY ✓
  - ANTHROPIC_API_KEY ✓
  - GOOGLE_API_KEY ✓
  - GEMINI_API_KEY ✓
  - REDIS_HOST=localhost ✓
  - REDIS_PORT=6379 ✓

### 3. Улучшена логика загрузки настроек
- ✅ [config/settings.py](config/settings.py) теперь поддерживает:
  - Doppler CLI (рекомендуется)
  - Doppler SDK (опционально)
  - .env файл (фоллбэк)

### 4. Созданы скрипты и документация
- ✅ [start.sh](start.sh) - быстрый запуск бота
- ✅ [stop.sh](stop.sh) - остановка сервисов
- ✅ [.env.example](.env.example) - шаблон переменных
- ✅ [QUICKSTART.md](QUICKSTART.md) - краткая инструкция
- ✅ [SETUP_GUIDE.md](SETUP_GUIDE.md) - подробное руководство

## 🚀 Как запустить (3 простых шага)

### Шаг 1: Запустите Redis

```bash
docker-compose up -d redis
```

### Шаг 2: Запустите бота

```bash
./start.sh
```

Или вручную:
```bash
doppler run --project rate-posts-bot --config dev -- venv/bin/python3 main.py
```

### Шаг 3: Настройте канал

1. Добавьте бота в канал как администратора
2. Получите ID канала через [@userinfobot](https://t.me/userinfobot)
3. Отправьте боту: `/add_channel <channel_id>`

## ⚙️  Редактирование промптов

Промпты находятся в [config/prompts.py](config/prompts.py). Просто отредактируйте нужный промпт и перезапустите бота!

**Пример - изменить промпт для Claude:**
```python
CLAUDE_EVALUATION_PROMPT = """Твой новый промпт здесь...

Пост:
{content}

Формат ответа: "Оценка: X/10. Комментарий."
"""
```

## 🔧 Полезные команды

### Проверка секретов Doppler
```bash
doppler secrets --project rate-posts-bot --config dev
```

### Проверка Redis
```bash
docker-compose exec redis redis-cli ping
# Должно вернуть: PONG
```

### Просмотр логов
```bash
# Логи бота (если запущен через ./start.sh)
# Будут видны в терминале

# Логи Redis
docker-compose logs -f redis
```

### Тест настроек
```bash
doppler run --project rate-posts-bot --config dev -- \
  venv/bin/python3 -c "from config.settings import settings; print('OK')"
```

## 📖 Дополнительная документация

- **Быстрый старт**: [QUICKSTART.md](QUICKSTART.md)
- **Подробная настройка**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Общая информация**: [README.md](README.md)

## 🐛 Troubleshooting

### Проблема: Redis connection refused
**Решение**: Запустите Redis
```bash
docker-compose up -d redis
```

### Проблема: ModuleNotFoundError
**Решение**: Установите зависимости
```bash
venv/bin/pip install -r requirements.txt
```

### Проблема: Validation error for Settings
**Решение**: Проверьте, что все секреты добавлены в Doppler
```bash
doppler secrets --project rate-posts-bot --config dev
```

## 🎯 Текущий статус

- ✅ Doppler настроен
- ✅ Все секреты добавлены
- ✅ Промпты разделены по LLM
- ✅ Скрипты запуска созданы
- ✅ Настройки протестированы
- 🔲 Redis нужно запустить
- 🔲 Бот готов к запуску

**Следующий шаг**: `./start.sh`
