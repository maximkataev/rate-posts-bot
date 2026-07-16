# Отладка отслеживания постов в каналах

## Проблема: Бот не ловит новые посты

### Шаг 1: Проверьте конфигурацию каналов

```bash
# Запустите скрипт проверки
doppler run --project rate-posts-bot --config dev -- venv/bin/python3 check-channels.py
```

Или через бота:
```
/list_channels
```

### Шаг 2: Проверьте права бота в канале

1. **Откройте канал в Telegram**
2. **Перейдите в настройки → Администраторы**
3. **Найдите вашего бота в списке**
4. **Проверьте права:**
   - ✅ "Публикация сообщений" должна быть включена
   - ✅ Бот должен быть администратором

### Шаг 3: Проверьте ID канала

```bash
# 1. Перешлите любое сообщение из канала боту @userinfobot
# 2. Скопируйте "Forwarded from chat" ID (должно начинаться с минуса)
# Пример: -1001234567890

# 3. Проверьте, что этот ID добавлен:
/list_channels
```

### Шаг 4: Посмотрите логи бота

Логи покажут, почему посты игнорируются:

```
# Запустите бота с логами
doppler run --project rate-posts-bot --config dev -- venv/bin/python3 main.py
```

**Что искать в логах:**

✅ **Пост обрабатывается:**
```
Processing post from channel -1001234567890 (message_id: 123)
```

❌ **Канал не отслеживается:**
```
Ignoring post from non-monitored channel -1001234567890 (title: My Channel)
```

❌ **Канал отключен:**
```
Channel -1001234567890 is disabled
```

### Шаг 5: Тестовый пост

После настройки опубликуйте тестовый пост:

1. **Опубликуйте текстовый пост** в канале
2. **Проверьте логи бота** - должно быть:
   ```
   Processing post from channel -1001234567890 (message_id: 123)
   ```
3. **Бот должен ответить** сообщением с оценкой

### Шаг 6: Типы поддерживаемых постов

Бот обрабатывает:
- ✅ Текстовые посты
- ✅ Посты с изображениями + текст
- ✅ Опросы (polls)

Бот игнорирует:
- ❌ Видео без текста
- ❌ Аудио
- ❌ Документы
- ❌ Стикеры
- ❌ Голосовые сообщения

### Частые проблемы

#### 1. "Ignoring post from non-monitored channel"
**Решение:** Канал не добавлен. Выполните:
```
/add_channel -1001234567890
```

#### 2. Бот не видит сообщения вообще
**Решение:** 
- Проверьте, что бот администратор канала
- Проверьте права бота (должны быть права на просмотр сообщений)
- Перезапустите бота

#### 3. "Channel is disabled"
**Решение:** Канал отключен в Redis. Проверьте конфигурацию:
```bash
doppler run -- venv/bin/python3 check-channels.py
```

#### 4. Бот ответил "Processing..." но не отправил оценку
**Проверьте:**
- API ключи настроены (OpenAI, Anthropic, Google)
- Логи на наличие ошибок от LLM API
- Баланс API ключей

### Отладочный режим

Для подробных логов запустите с DEBUG уровнем:

```bash
# Временно установите DEBUG уровень
doppler secrets set LOG_LEVEL="DEBUG" --project rate-posts-bot --config dev

# Запустите бота
doppler run --project rate-posts-bot --config dev -- venv/bin/python3 main.py

# После отладки верните обратно INFO
doppler secrets set LOG_LEVEL="INFO" --project rate-posts-bot --config dev
```

### Быстрая проверка

```bash
# 1. Проверьте каналы
doppler run -- venv/bin/python3 check-channels.py

# 2. Проверьте Redis
redis-cli ping

# 3. Проверьте Doppler секреты
doppler secrets --project rate-posts-bot --config dev | grep -E "TELEGRAM|OPENAI|ANTHROPIC|GOOGLE"

# 4. Запустите бота и опубликуйте тестовый пост
```
