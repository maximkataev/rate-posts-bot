# Установка Redis

У вас не установлен ни Docker, ни Redis. Выберите один из вариантов:

## Вариант 1: Docker Desktop (рекомендуется)

**Плюсы**: изолированная среда, легко удалить, не влияет на систему
**Минусы**: требует больше ресурсов

### Установка:
```bash
# 1. Скачайте Docker Desktop для macOS
# https://www.docker.com/products/docker-desktop

# 2. Установите приложение

# 3. Запустите Docker Desktop

# 4. Проверьте установку
docker --version
docker compose version

# 5. Запустите бота
./start.sh
```

## Вариант 2: Redis через Homebrew (легче)

**Плюсы**: быстрая установка, меньше ресурсов
**Минусы**: устанавливается в систему

### Установка:
```bash
# 1. Установите Redis
brew install redis

# 2. Запустите Redis
brew services start redis

# 3. Проверьте
redis-cli ping
# Должно вернуть: PONG

# 4. Запустите бота
./start-local.sh
```

## Вариант 3: Без установки (использовать .env файл)

Если не хотите устанавливать Redis прямо сейчас:

```bash
# 1. Создайте .env файл
cp .env.example .env

# 2. Заполните API ключи в .env
nano .env

# 3. Установите и запустите Redis позже
# А пока бот будет использовать настройки из .env
```

## Какой вариант выбрать?

- **Для разработки**: Docker Desktop
- **Для быстрого тестирования**: Redis через Homebrew  
- **Если не уверены**: Redis через Homebrew (проще начать)

## После установки Redis:

```bash
# С Docker:
./start.sh

# С Homebrew Redis:
./start-local.sh

# Оба варианта запустят бота с вашими настройками из Doppler
```
