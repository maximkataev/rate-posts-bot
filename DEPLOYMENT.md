# Руководство по деплою

## Быстрый старт (5 минут)

### 1. Клонирование и настройка

```bash
git clone <your-repo>
cd telegram-post-evaluator

# Создать .env из шаблона
cp .env.example .env

# Отредактировать .env
nano .env
```

### 2. Получение API ключей

#### Telegram Bot Token
1. Откройте [@BotFather](https://t.me/botfather)
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

#### OpenAI API Key
1. [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Скопируйте в `.env`

#### Anthropic API Key
1. [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
2. Create Key
3. Скопируйте в `.env`

#### Google API Key (Gemini)
1. [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Create API key
3. Скопируйте в `.env`

### 3. Запуск

#### Вариант A: Docker (рекомендуется)

```bash
# Запуск
docker-compose up -d

# Проверка логов
docker-compose logs -f bot

# Остановка
docker-compose down
```

#### Вариант B: Локально

```bash
# Автоматическая установка и запуск
./start.sh

# Или вручную
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### Вариант C: Systemd Service (Linux)

```bash
# Установка сервиса
sudo ./install-service.sh

# Управление
sudo systemctl start telegram-post-evaluator
sudo systemctl status telegram-post-evaluator
sudo journalctl -u telegram-post-evaluator -f
```

---

## Production Deployment

### VPS (Ubuntu 22.04)

```bash
# 1. Обновление системы
sudo apt update && sudo apt upgrade -y

# 2. Установка зависимостей
sudo apt install -y python3 python3-pip python3-venv redis-server git

# 3. Клонирование репозитория
git clone <your-repo> /opt/telegram-post-evaluator
cd /opt/telegram-post-evaluator

# 4. Настройка .env
sudo cp .env.example .env
sudo nano .env

# 5. Установка как systemd service
sudo ./install-service.sh

# 6. Проверка
sudo systemctl status telegram-post-evaluator
```

### Docker на сервере

```bash
# 1. Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Клонирование и запуск
git clone <your-repo> /opt/telegram-post-evaluator
cd /opt/telegram-post-evaluator
cp .env.example .env
nano .env

docker-compose up -d
```

### Автоматический перезапуск при падении

Docker Compose уже настроен на `restart: unless-stopped`.

Для systemd service:
```bash
sudo systemctl enable telegram-post-evaluator
```

---

## Использование Doppler

### Локальная разработка

```bash
# Установка Doppler CLI
brew install dopplerhq/cli/doppler  # macOS
# или
curl -sLf https://cli.doppler.com/install.sh | sh

# Логин
doppler login

# Настройка проекта
doppler setup

# Добавление секретов
doppler secrets set TELEGRAM_BOT_TOKEN="your_token"
doppler secrets set OPENAI_API_KEY="your_key"
doppler secrets set ANTHROPIC_API_KEY="your_key"
doppler secrets set GOOGLE_API_KEY="your_key"

# Запуск с Doppler
doppler run -- python main.py
```

### Production с Doppler

```bash
# Service Token для production
doppler configs tokens create production --config prd

# Добавить в systemd service
[Service]
Environment="DOPPLER_TOKEN=dp.st.xxx"
ExecStart=/usr/local/bin/doppler run -- /path/to/venv/bin/python /path/to/main.py
```

---

## Настройка канала

### 1. Добавление бота в канал

1. Откройте канал → Настройки → Администраторы
2. Добавить администратора → Найти бота
3. Включить права:
   - ✅ Публикация сообщений
   - ❌ Остальное не обязательно

### 2. Получение ID канала

**Способ 1: Через @userinfobot**
1. Перешлите любое сообщение из канала боту [@userinfobot](https://t.me/userinfobot)
2. Скопируйте "Forwarded from chat" ID (например: `-1001234567890`)

**Способ 2: Через @getidsbot**
1. Перешлите сообщение боту [@getidsbot](https://t.me/getidsbot)
2. Скопируйте Chat ID

**Способ 3: Вручную из URL**
- Если URL канала: `https://t.me/c/1234567890/123`
- ID канала: `-100` + `1234567890` = `-1001234567890`

### 3. Регистрация канала

```
/add_channel -1001234567890
```

---

## Monitoring

### Логи

```bash
# Docker
docker-compose logs -f bot

# Systemd
sudo journalctl -u telegram-post-evaluator -f

# Локально
tail -f bot.log
```

### Redis

```bash
# Подключение к Redis
redis-cli

# Или в Docker
docker-compose exec redis redis-cli

# Просмотр всех каналов
SMEMBERS channels:all

# Просмотр конфига канала
GET channel:-1001234567890
```

### Backup

```bash
# Backup Redis данных
python redis_utils.py backup backup.json

# Restore
python redis_utils.py restore backup.json

# Список каналов
python redis_utils.py list
```

---

## Troubleshooting

### Бот не отвечает

```bash
# Проверка статуса
docker-compose ps
# или
sudo systemctl status telegram-post-evaluator

# Проверка логов
docker-compose logs --tail=50 bot
```

### Redis не подключается

```bash
# Проверка Redis
redis-cli ping
# Должно вернуть: PONG

# Если не работает
sudo systemctl restart redis-server
```

### LLM API ошибки

```bash
# Проверка .env
cat .env | grep API_KEY

# Тест API ключей
python test_evaluation.py
```

### Нет оценок постов

1. Проверьте, что бот администратор канала
2. Проверьте права на публикацию сообщений
3. Проверьте, что канал добавлен: `/list_channels`
4. Проверьте логи на ошибки API

---

## Обновление

```bash
# Docker
cd /opt/telegram-post-evaluator
git pull
docker-compose down
docker-compose build
docker-compose up -d

# Systemd
cd /opt/telegram-post-evaluator
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-post-evaluator
```

---

## Безопасность

### Рекомендации

1. **Не коммитьте .env в Git**
   - Добавлено в `.gitignore`
   - Используйте Doppler для секретов

2. **Ограничьте доступ к Redis**
   ```bash
   # В production используйте пароль
   redis-cli CONFIG SET requirepass "strong_password"
   ```

3. **Файрвол**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

4. **Регулярные обновления**
   ```bash
   sudo apt update && sudo apt upgrade -y
   pip install --upgrade -r requirements.txt
   ```

5. **Мониторинг API квот**
   - Проверяйте использование API ключей
   - Настройте лимиты в Dashboard провайдеров

---

## Масштабирование

### Несколько ботов

```bash
# Создайте отдельные .env для каждого бота
cp .env .env.bot1
cp .env .env.bot2

# Запустите с разными конфигами
docker-compose -f docker-compose.bot1.yml up -d
docker-compose -f docker-compose.bot2.yml up -d
```

### Load Balancing Redis

Используйте Redis Cluster или Sentinel для high availability.

### Rate Limiting

Настройте ограничения в `config/settings.py` для контроля частоты запросов к API.

---

## Поддержка

- Telegram: [@maksimkin](https://t.me/maksimkin)
- Issues: GitHub Issues
- Документация: README.md
