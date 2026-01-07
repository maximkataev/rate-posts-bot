# Инструкция по локальному запуску проекта

## 1. Установка Redis

### Вариант A: Через Homebrew (macOS)
```bash
# Установка Redis
brew install redis

# Запуск Redis
brew services start redis

# Проверка работы
redis-cli ping
# Ожидается ответ: PONG
```

### Вариант B: Через Docker
```bash
# Запуск Redis в контейнере
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Проверка работы
docker exec redis redis-cli ping
# Ожидается ответ: PONG
```

### Вариант C: Через docker-compose (рекомендуется для локальной разработки)
```bash
# Запустить только Redis из docker-compose.yml
docker-compose up -d redis

# Проверка работы
docker-compose exec redis redis-cli ping
# Ожидается ответ: PONG
```

## 2. Настройка окружения

### Вариант A: Использование Doppler (рекомендуется)

```bash
# Проверка установки Doppler
doppler --version

# Если не установлен:
brew install dopplerhq/cli/doppler

# Авторизация (если еще не авторизованы)
doppler login

# Перейти в директорию проекта
cd /Users/maximkataev/Desktop/rate_posts_bot

# Установка проекта и конфигурации
doppler setup --project rate-posts-bot --config dev

# Проверка секретов
doppler secrets
```

### Вариант B: Использование .env файла

```bash
# Создать .env на основе примера
cp .env.example .env

# Отредактировать .env и добавить свои ключи
nano .env
```

## 3. Проверка и добавление недостающих секретов в Doppler

```bash
# Проверка текущих секретов
doppler secrets --project rate-posts-bot --config dev

# Добавление недостающих секретов (если нужно)
doppler secrets set OPENAI_API_KEY="sk-..." --project rate-posts-bot --config dev
doppler secrets set REDIS_HOST="localhost" --project rate-posts-bot --config dev
doppler secrets set REDIS_PORT="6379" --project rate-posts-bot --config dev
doppler secrets set REDIS_DB="0" --project rate-posts-bot --config dev
doppler secrets set OPENAI_MODEL="gpt-4o" --project rate-posts-bot --config dev
doppler secrets set ANTHROPIC_MODEL="claude-sonnet-4-20250514" --project rate-posts-bot --config dev
doppler secrets set GEMINI_MODEL="gemini-2.0-flash-exp" --project rate-posts-bot --config dev
doppler secrets set LOG_LEVEL="INFO" --project rate-posts-bot --config dev
```

## 4. Установка зависимостей Python

```bash
# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

## 5. Запуск бота

### С Doppler:
```bash
# Убедитесь, что Redis запущен
redis-cli ping

# Запуск бота через Doppler
doppler run -- python main.py
```

### С .env файлом:
```bash
# Убедитесь, что Redis запущен
redis-cli ping

# Запуск бота напрямую
python main.py
```

## 6. Проверка работы

### Тестирование подключения к Redis:
```bash
python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); print('Redis OK:', r.ping())"
```

### Тестирование загрузки настроек:
```bash
# С Doppler
doppler run -- python -c "from config.settings import settings; print('Settings loaded:', settings.telegram_bot_token[:10])"

# Без Doppler
python -c "from config.settings import settings; print('Settings loaded:', settings.telegram_bot_token[:10])"
```

## 7. Настройка бота в Telegram

1. **Добавьте бота в канал:**
   - Откройте настройки канала
   - Администраторы → Добавить администратора
   - Найдите вашего бота
   - Дайте права на **публикацию сообщений**

2. **Получите ID канала:**
   - Перешлите сообщение из канала боту [@userinfobot](https://t.me/userinfobot)
   - Скопируйте "Forwarded from chat" (например: `-1001234567890`)

3. **Зарегистрируйте канал:**
   ```
   /add_channel -1001234567890
   ```

## 8. Полезные команды для отладки

```bash
# Просмотр логов Redis
docker-compose logs -f redis

# Проверка данных в Redis
redis-cli
> KEYS *
> GET channel:-1001234567890

# Просмотр работы бота с debug логами
doppler run -- python main.py --log-level DEBUG

# Проверка подключения к LLM API
python test_evaluation.py
```

## 9. Решение частых проблем

### Redis connection refused
```bash
# Проверьте, что Redis запущен
redis-cli ping

# Если не запущен
brew services start redis
# или
docker-compose up -d redis
```

### Doppler не находит секреты
```bash
# Проверьте настройку проекта
doppler setup

# Проверьте секреты
doppler secrets
```

### ModuleNotFoundError
```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate

# Переустановите зависимости
pip install -r requirements.txt
```

## 10. Структура промптов (новое!)

Теперь промпты для каждой LLM хранятся в отдельном файле [config/prompts.py](config/prompts.py):

- **OpenAI**: базовый промпт
- **Claude**: критичный рецензент (может занизить оценку)
- **Gemini**: подбадривающий рецензент

Вы можете легко изменять промпты для каждой модели отдельно!

## Альтернативный способ: Docker Compose (всё вместе)

Если хотите запустить всё в Docker (включая бота):

```bash
# Создайте .env файл
cp .env.example .env
nano .env

# Запустите всё
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot
```
