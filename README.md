# Telegram Post Evaluator Bot

Телеграм-бот для автоматической оценки постов в каналах с помощью нескольких AI моделей (GPT-4, Claude, Gemini).

## Возможности

- 🤖 Оценка постов 3-5 различными LLM моделями одновременно
- 📊 Агрегация оценок и вычисление средней
- 🖼️ Поддержка текстовых постов, изображений и опросов
- 💾 Хранение конфигурации каналов в Redis
- 🔐 Управление креденшалами через Doppler
- ⚡ Асинхронная обработка запросов
- 📝 Кастомизация промптов для оценки

## Технологический стек

- **aiogram 3.x** - фреймворк для Telegram Bot API
- **Redis** - хранение конфигурации
- **OpenAI API** - GPT-4
- **Anthropic API** - Claude
- **Google Generative AI** - Gemini
- **Doppler** - управление секретами

## Установка

### Требования

- Python 3.11+
- Redis 6.0+
- API ключи для LLM провайдеров

### Шаг 1: Клонирование и установка зависимостей

```bash
git clone <your-repo>
cd telegram-post-evaluator

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

### Шаг 2: Настройка Redis

```bash
# Установка Redis (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install redis-server

# Запуск Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверка
redis-cli ping
# Должно вернуть: PONG
```

Для macOS:
```bash
brew install redis
brew services start redis
```

### Шаг 3: Получение API ключей

1. **Telegram Bot Token**
   - Создайте бота через [@BotFather](https://t.me/botfather)
   - Команда: `/newbot`
   - Скопируйте токен

2. **OpenAI API Key**
   - Зарегистрируйтесь на [platform.openai.com](https://platform.openai.com)
   - Создайте API ключ в разделе API Keys

3. **Anthropic API Key**
   - Зарегистрируйтесь на [console.anthropic.com](https://console.anthropic.com)
   - Создайте API ключ

4. **Google API Key (Gemini)**
   - Перейдите в [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Создайте API ключ

### Шаг 4: Конфигурация

#### Вариант A: Использование .env файла

```bash
cp .env.example .env
# Отредактируйте .env и добавьте свои ключи
nano .env
```

#### Вариант B: Использование Doppler

```bash
# Установка Doppler CLI
brew install dopplerhq/cli/doppler  # macOS
# или
curl -sLf --retry 3 --tlsv1.2 --proto "=https" https://cli.doppler.com/install.sh | sh

# Авторизация
doppler login

# Настройка проекта
doppler setup

# Добавление секретов
doppler secrets set TELEGRAM_BOT_TOKEN="your_token"
doppler secrets set OPENAI_API_KEY="your_key"
# ... и т.д.

# Запуск с Doppler
doppler run -- python main.py
```

## Использование

### Запуск бота

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запуск
python main.py

# Или с Doppler
doppler run -- python main.py
```

### Настройка канала

1. **Добавьте бота в канал**
   - Откройте настройки канала
   - Администраторы → Добавить администратора
   - Найдите и добавьте вашего бота
   - Дайте права на **публикацию сообщений**

2. **Получите ID канала**
   - Перешлите любое сообщение из канала боту [@userinfobot](https://t.me/userinfobot)
   - Скопируйте значение "Forwarded from chat" (например: `-1001234567890`)

3. **Зарегистрируйте канал**
   - Отправьте боту команду:
   ```
   /add_channel -1001234567890
   ```

### Команды бота

- `/start` - Начало работы с ботом
- `/help` - Справка по использованию
- `/add_channel <channel_id>` - Добавить канал для мониторинга
- `/remove_channel <channel_id>` - Удалить канал из мониторинга
- `/list_channels` - Список отслеживаемых каналов

## Как это работает

1. Бот мониторит новые посты в добавленных каналах
2. При появлении нового поста (текст, изображение, опрос):
   - Извлекается контент
   - Отправляется запрос ко всем настроенным LLM моделям параллельно
   - Каждая модель оценивает пост по 10-балльной шкале
   - Вычисляется средняя оценка
3. Бот публикует оценку как ответ на исходный пост

### Пример оценки

```
📊 Оценка поста (3 моделей):

🎯 Средняя оценка: 8.3/10

🟢 OpenAI GPT: 9/10
   💬 Отличный контент с практическими примерами

🟢 Claude: 8/10
   💬 Информативно и хорошо структурировано

🟡 Gemini: 8/10
   💬 Полезная информация, но можно добавить больше деталей
```

## Поддерживаемые типы контента

✅ **Поддерживаются:**
- Текстовые посты
- Посты с изображениями
- Посты с текстом и изображениями
- Опросы

❌ **Игнорируются:**
- Видео
- Аудио
- Документы
- Стикеры
- Анимации

## Структура проекта

```
telegram-post-evaluator/
├── config/
│   └── settings.py          # Конфигурация и Doppler
├── src/
│   ├── bot.py               # Инициализация бота
│   ├── handlers/
│   │   ├── admin.py         # Админские команды
│   │   └── channel.py       # Обработка постов
│   ├── services/
│   │   ├── redis_service.py # Redis операции
│   │   └── llm_service.py   # Интеграция с LLM
│   └── utils/
├── main.py                  # Точка входа
└── requirements.txt
```

## Расширенная конфигурация

### Кастомизация промпта

Вы можете изменить промпт для оценки в `config/settings.py`:

```python
evaluation_prompt_template: str = """
Оцени этот пост по 10-балльной шкале...
"""
```

### Настройка моделей

В `config/settings.py` можно изменить используемые модели:

```python
openai_model: str = "gpt-4-turbo"
anthropic_model: str = "claude-3-5-sonnet-20241022"
gemini_model: str = "gemini-pro"
```

### Добавление новых LLM провайдеров

Добавьте новый метод в `src/services/llm_service.py`:

```python
async def evaluate_with_your_model(
    self,
    content: str,
    image_url: Optional[str] = None,
    custom_prompt: Optional[str] = None
) -> EvaluationResult:
    # Ваша реализация
    pass
```

## Мониторинг и логи

Бот логирует все важные события:

```bash
# Просмотр логов в реальном времени
tail -f app.log

# Уровень логирования можно изменить в .env
LOG_LEVEL=DEBUG
```

## Production Deployment

### Systemd Service (Linux)

Создайте файл `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Post Evaluator Bot
After=network.target redis.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram-post-evaluator
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  bot:
    build: .
    env_file: .env
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

## Troubleshooting

### Бот не видит сообщения в канале

- Убедитесь, что бот добавлен как администратор
- Проверьте права на публикацию сообщений
- Канал должен быть добавлен через `/add_channel`

### Ошибки API ключей

```bash
# Проверьте наличие ключей
python -c "from config.settings import settings; print(settings.openai_api_key)"
```

### Redis connection failed

```bash
# Проверьте статус Redis
redis-cli ping

# Проверьте подключение
redis-cli -h localhost -p 6379
```

### LLM модель не отвечает

- Проверьте баланс API
- Проверьте rate limits
- Убедитесь, что модель доступна в вашем регионе

## Безопасность

- ⚠️ **Никогда** не коммитьте `.env` файл в Git
- Используйте Doppler или другой секрет-менеджер в production
- Регулярно ротируйте API ключи
- Ограничьте доступ к Redis

## Лицензия

MIT

## Поддержка

По вопросам и предложениям: [@maksimkin](https://t.me/maksimkin)

## TODO

- [ ] Поддержка изображений через CDN
- [ ] Web dashboard для управления
- [ ] Статистика оценок
- [ ] A/B тестирование промптов
- [ ] Webhook mode вместо polling
- [ ] Поддержка групповых чатов
- [ ] Расписание оценок
- [ ] Интеграция с аналитикой
