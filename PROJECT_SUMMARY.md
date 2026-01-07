# Telegram Post Evaluator Bot - Краткое резюме проекта

## 📦 Что создано

Полнофункциональный телеграм-бот для автоматической оценки постов в каналах с помощью нескольких AI моделей.

## 🎯 Основной функционал

1. **Мониторинг каналов** - отслеживание новых постов в Telegram каналах
2. **Мультимодельная оценка** - параллельная оценка постов через:
   - OpenAI GPT-4
   - Anthropic Claude Sonnet 4
   - Google Gemini 2.0 Flash
3. **Агрегация результатов** - вычисление средней оценки и публикация в канале
4. **Управление** - команды для добавления/удаления каналов
5. **Хранение конфигурации** - Redis для хранения списка каналов

## 📂 Структура проекта

```
telegram-post-evaluator/
├── config/
│   └── settings.py              # Настройки из Doppler/env
├── src/
│   ├── bot.py                   # Инициализация бота
│   ├── handlers/
│   │   ├── admin.py             # Команды управления
│   │   └── channel.py           # Обработка постов
│   ├── services/
│   │   ├── redis_service.py     # Redis операции
│   │   └── llm_service.py       # Интеграция с LLM
│   └── utils/
├── main.py                      # Точка входа
├── requirements.txt             # Зависимости
├── .env.example                 # Шаблон переменных окружения
├── Dockerfile                   # Docker образ
├── docker-compose.yml           # Docker Compose конфигурация
├── Makefile                     # Команды для разработки
├── start.sh                     # Скрипт быстрого старта
├── install-service.sh           # Установка systemd service
├── redis_utils.py               # Backup/restore Redis
├── test_evaluation.py           # Тест оценки постов
├── README.md                    # Основная документация
└── DEPLOYMENT.md                # Руководство по деплою
```

## 🚀 Быстрый старт

### Минимальная настройка (3 шага)

1. **Клонирование и создание .env**
   ```bash
   git clone <repo>
   cd telegram-post-evaluator
   cp .env.example .env
   nano .env  # Добавить API ключи
   ```

2. **Запуск с Docker**
   ```bash
   docker-compose up -d
   ```

3. **Добавление канала**
   - Добавить бота администратором в канал
   - Получить ID канала через @userinfobot
   - Отправить боту: `/add_channel -1001234567890`

### Альтернативные варианты запуска

**Локально (Python)**
```bash
./start.sh
```

**Systemd Service (Linux)**
```bash
sudo ./install-service.sh
sudo systemctl start telegram-post-evaluator
```

**С Doppler**
```bash
doppler run -- python main.py
```

## 🔑 Необходимые API ключи

1. **Telegram Bot Token** - [@BotFather](https://t.me/botfather)
2. **OpenAI API Key** - [platform.openai.com](https://platform.openai.com/api-keys)
3. **Anthropic API Key** - [console.anthropic.com](https://console.anthropic.com/settings/keys)
4. **Google API Key** - [makersuite.google.com](https://makersuite.google.com/app/apikey)

## 📋 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и инструкции |
| `/help` | Справка по использованию |
| `/add_channel <id>` | Добавить канал для мониторинга |
| `/remove_channel <id>` | Удалить канал |
| `/list_channels` | Список всех каналов |

## 🛠 Утилиты разработки

### Makefile команды

```bash
make install         # Установить зависимости
make run            # Запустить бота локально
make docker-up      # Запустить в Docker
make docker-logs    # Просмотр логов
make redis-cli      # Подключиться к Redis
make test           # Запустить тесты
make clean          # Очистить кэш
```

### Redis утилиты

```bash
python redis_utils.py backup backup.json    # Backup
python redis_utils.py restore backup.json   # Restore
python redis_utils.py list                  # Список каналов
```

### Тестирование

```bash
python test_evaluation.py  # Тест оценки постов
```

## 📊 Пример работы

```
Пользователь публикует в канале:
┌─────────────────────────────────┐
│ 🚀 Новая функция в приложении!  │
│ Теперь можно делиться постами   │
│ в соцсети одним нажатием 👇     │
└─────────────────────────────────┘
              ↓
    Бот получает уведомление
              ↓
  Параллельный запрос к 3-4 LLM
              ↓
┌─────────────────────────────────┐
│ 📊 Оценка поста (3 моделей):    │
│                                 │
│ 🎯 Средняя оценка: 8.3/10       │
│                                 │
│ 🟢 OpenAI GPT: 9/10             │
│    💬 Отличный контент...       │
│                                 │
│ 🟢 Claude: 8/10                 │
│    💬 Информативно и хорошо...  │
│                                 │
│ 🟡 Gemini: 8/10                 │
│    💬 Полезная информация...    │
└─────────────────────────────────┘
```

## 🎨 Особенности реализации

### Архитектурные решения

- **Асинхронность** - полностью async/await для максимальной производительности
- **Параллелизм** - одновременные запросы к всем LLM через asyncio.gather
- **Модульность** - разделение на handlers, services, utils
- **Конфигурируемость** - все настройки через env/Doppler
- **Надёжность** - обработка ошибок, retry, graceful shutdown

### Технические детали

- **aiogram 3.x** - современный асинхронный фреймворк
- **Redis** - хранение конфигурации каналов
- **httpx** - асинхронные HTTP запросы
- **Pydantic** - валидация конфигурации
- **Docker** - контейнеризация для простого деплоя

## 🔒 Безопасность

- ✅ Секреты через Doppler или .env (не в Git)
- ✅ Redis с возможностью установки пароля
- ✅ Docker контейнеры с минимальными правами
- ✅ Systemd service с ограничениями безопасности
- ✅ Валидация входных данных

## 📈 Возможности расширения

### Уже реализовано
- ✅ Поддержка 3-4 LLM провайдеров
- ✅ Кастомные промпты для каждого канала
- ✅ Backup/restore конфигурации
- ✅ Docker и systemd деплой
- ✅ Graceful shutdown

### Можно добавить
- [ ] Webhook mode вместо polling
- [ ] Web dashboard для управления
- [ ] Статистика оценок
- [ ] A/B тестирование промптов
- [ ] Поддержка видео через транскрипцию
- [ ] Scheduled evaluations
- [ ] Уведомления о низких оценках
- [ ] Интеграция с аналитикой

## 📚 Документация

- **README.md** - основная документация, функционал, установка
- **DEPLOYMENT.md** - подробное руководство по деплою
- **Комментарии в коде** - все модули хорошо документированы
- **Type hints** - везде используются аннотации типов

## 🐛 Troubleshooting

Типичные проблемы и решения:

1. **Бот не видит посты** → Проверить права администратора
2. **Redis ошибка** → Проверить `redis-cli ping`
3. **API ошибки** → Проверить ключи и квоты
4. **Нет оценок** → Проверить логи `docker-compose logs -f`

## 💡 Лучшие практики использования

1. **Запуск в production** → Docker Compose или systemd service
2. **Секреты** → Использовать Doppler, не .env файлы
3. **Мониторинг** → Настроить просмотр логов
4. **Backup** → Регулярные backup Redis через `redis_utils.py`
5. **Обновления** → Следить за обновлениями зависимостей

## 📞 Контакты и поддержка

- Разработчик: [@maksimkin](https://t.me/maksimkin)
- GitHub: <ссылка на репозиторий>
- Issues: GitHub Issues

## 📄 Лицензия

MIT License - свободное использование и модификация

---

## ✅ Чеклист готовности к использованию

- [x] Код написан и протестирован
- [x] Документация создана (README, DEPLOYMENT)
- [x] Docker конфигурация готова
- [x] Systemd service файл создан
- [x] Скрипты установки и запуска
- [x] Утилиты для backup/restore
- [x] Примеры конфигурации (.env.example)
- [x] .gitignore настроен
- [x] Makefile с полезными командами

**Проект полностью готов к использованию!** 🚀
