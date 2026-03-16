# PRD — Card Management Panel + Multi-Device Web-Scrcpy
**Version:** 2.0  
**Date:** 2026-03-16  
**Status:** Final Draft  

---

## 1. Обзор и цели

Система состоит из двух независимых частей, работающих на одном Windows 11 хосте:

**Часть A — Web-Scrcpy (хост, вне Docker):**  
Модифицированный форк [baixin1228/web-scrcpy](https://github.com/baixin1228/web-scrcpy). Запускается скриптом на хосте Windows. Поддерживает множество ADB-устройств одновременно, эксклюзивные сессии и авто-отключение по таймауту. Доступен публично через nginx на 80 порту.

**Часть B — Card Management Panel (Docker):**  
Локальная система управления банковскими картами, транзакциями и устройствами. Включает FastAPI-backend, React-frontend, PostgreSQL, Redis, Telegram-бот. Доступна только на `localhost:8000` (FastAPI) и `localhost:3000` (React dev) / через nginx внутренне.

---

## 2. Целевая аудитория

Единственный пользователь — администратор системы. Авторизация в Phase 1 не требуется.

---

## 3. Общая архитектура

```
Windows 11 Host
│
├── [ХОС] web-scrcpy (Flask, порт 5000)
│         └── запускается start-scrcpy.bat
│         └── ADB + scrcpy процессы для каждого устройства
│
├── [DOCKER] nginx (порт 80, публично)
│         └── proxy_pass → host:5000 (web-scrcpy)
│
├── [DOCKER] fastapi (порт 8000, только localhost)
│         └── onion: router → service → repository
│         └── SQLAlchemy 2.0 async + Alembic
│
├── [DOCKER] react-frontend (порт 3000 dev / nginx prod)
│         └── Vite + React + useState/Context
│
├── [DOCKER] telegram-bot (aiogram 3, Polling)
│         └── добавление карт (Phase 1)
│         └── парсинг транзакций (Phase 2)
│
├── [DOCKER] postgresql (порт 5432, internal)
├── [DOCKER] redis (порт 6379, internal)
└── .env → pydantic-settings во всех сервисах
```

**Связи между сервисами:**
- React → FastAPI: `http://localhost:8000/api/v1/...`
- Telegram-бот → FastAPI: `http://fastapi:8000/api/v1/...` (внутри Docker-сети)
- FastAPI → PostgreSQL: asyncpg через SQLAlchemy
- FastAPI → Redis: aioredis (сессии устройств, настройки кэш)
- nginx → web-scrcpy: `http://host.docker.internal:5000`

---

## 4. Структура проекта

```
project-root/
│
├── docker-compose.yml
├── .env                          # все секреты и конфиги
├── .env.example
│
├── web-scrcpy/                   # ЧАСТЬ A — хост, вне Docker
│   ├── app.py                    # Flask + multi-device роутинг
│   ├── device_manager.py         # запуск/остановка scrcpy процессов
│   ├── session_manager.py        # Redis-блокировки сессий
│   ├── templates/
│   │   ├── index.html            # список устройств
│   │   └── device.html           # управление устройством + WS + inactivity
│   ├── requirements.txt
│   └── start-scrcpy.bat          # скрипт запуска на Windows
│
├── backend/                      # ЧАСТЬ B — FastAPI (Docker)
│   ├── Dockerfile
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py               # FastAPI app, lifespan, routers
│   │   ├── core/
│   │   │   ├── config.py         # pydantic-settings, .env
│   │   │   ├── database.py       # async engine, session factory
│   │   │   └── redis.py          # aioredis client
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py     # include всех роутеров
│   │   │       ├── cards.py
│   │   │       ├── transactions.py
│   │   │       ├── devices.py
│   │   │       └── settings.py
│   │   ├── services/             # бизнес-логика
│   │   │   ├── card_service.py
│   │   │   ├── transaction_service.py
│   │   │   ├── device_service.py
│   │   │   └── settings_service.py
│   │   ├── repositories/         # слой данных
│   │   │   ├── card_repository.py
│   │   │   ├── transaction_repository.py
│   │   │   └── settings_repository.py
│   │   ├── models/               # SQLAlchemy ORM модели
│   │   │   ├── base.py
│   │   │   ├── card.py
│   │   │   ├── transaction.py
│   │   │   └── setting.py
│   │   └── schemas/              # Pydantic схемы (request/response)
│   │       ├── card.py
│   │       ├── transaction.py
│   │       └── setting.py
│   └── requirements.txt
│
├── frontend/                     # React (Docker)
│   ├── Dockerfile
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/                  # fetch-обёртки
│       │   ├── cards.js
│       │   ├── transactions.js
│       │   ├── devices.js
│       │   └── settings.js
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.jsx
│       │   │   └── Header.jsx
│       │   ├── cards/
│       │   │   ├── CardsTable.jsx
│       │   │   ├── CardModal.jsx
│       │   │   └── CardForm.jsx
│       │   ├── transactions/
│       │   │   └── TransactionsTable.jsx
│       │   ├── devices/
│       │   │   └── DevicesTable.jsx
│       │   └── settings/
│       │       └── SettingsPanel.jsx
│       └── context/
│           └── AppContext.jsx
│
├── telegram-bot/                 # aiogram 3 (Docker)
│   ├── Dockerfile
│   ├── bot.py
│   ├── handlers/
│   │   ├── card_add.py           # Phase 1: добавление карт
│   │   └── transactions.py       # Phase 2: парсинг транзакций
│   ├── services/
│   │   └── gemini_client.py
│   └── requirements.txt
│
└── nginx/
    └── nginx.conf
```

---

## 5. Часть A — Web-Scrcpy (модификация)

### 5.1 Multi-device поддержка

**Текущее поведение оригинала:** при >1 подключённом устройстве — ошибка.

**Требуемое поведение:**

`device_manager.py` при старте и каждые 30 сек выполняет `adb devices`, получает список серийных номеров и:
- Для новых устройств: запускает `subprocess.Popen(['scrcpy', '--serial', device_id, ...], shell=False)`
- Для отключённых: завершает процесс через `process.terminate()` + `process.wait()`
- Хранит словарь `{device_id: process}` в памяти

**Маршрутизация Flask:**
```
GET /                  → список всех активных устройств (index.html)
GET /<device_id>       → страница управления устройством (device.html)
POST /api/release/<device_id>  → снять Redis-блокировку
GET /api/devices       → JSON список устройств и их статусов
```

**Acceptance criteria:**
- 5 устройств подключены → 5 независимых URL работают одновременно
- Физическое отключение устройства → страница показывает "Устройство недоступно"
- Подключение нового устройства → появляется без перезапуска сервера

### 5.2 Эксклюзивный доступ через Redis

```
Ключ:    session:lock:{device_id}
Значение: {"session_id": "uuid", "connected_at": "ISO timestamp"}
TTL:     inactivity_timeout_minutes * 60 (секунды)
```

**Логика при открытии `/<device_id>`:**
1. Проверить ключ в Redis
2. Если нет → создать сессию, записать ключ, показать страницу устройства
3. Если есть → показать страницу "Устройство занято" с авто-обновлением каждые 15 сек

**Acceptance criteria:**
- Два браузера не могут одновременно управлять одним устройством
- Разные устройства — независимые сессии, блокируются отдельно

### 5.3 Inactivity-таймер (в device.html, внутри WebSocket-объекта)

Значение таймаута запрашивается при загрузке страницы через `GET /api/settings/inactivity_timeout` из FastAPI (FastAPI отдаёт настройку из БД).

```javascript
// device.html — инициализация WebSocket и inactivity-логики
const socket = new WebSocket(`ws://${location.host}/ws/${deviceId}`);
let inactivityTimer;

async function loadTimeout() {
  const res = await fetch('http://localhost:8000/api/v1/settings/inactivity_timeout');
  const { value } = await res.json();
  return parseInt(value) * 60 * 1000; // минуты → мс
}

async function initInactivity() {
  const timeout = await loadTimeout();

  function reset() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
      socket.close();
      showMessage("Сессия завершена из-за неактивности");
      fetch(`/api/release/${deviceId}`, { method: 'POST' });
    }, timeout);
  }

  ['mousemove', 'keydown', 'touchstart', 'click'].forEach(e =>
    document.addEventListener(e, reset)
  );

  socket.onopen = () => reset();
  socket.onclose = () => {
    fetch(`/api/release/${deviceId}`, { method: 'POST' });
  };
}

initInactivity();
```

**Acceptance criteria:**
- Таймаут берётся из настроек панели (не хардкодится)
- При истечении таймаута → WebSocket закрывается, Redis-блокировка снимается
- Другой пользователь может подключиться сразу после авто-отключения

### 5.4 Запуск на Windows 11

**`start-scrcpy.bat`:**
```bat
@echo off
echo Checking ADB...
adb version || (echo ADB not found in PATH & pause & exit)
echo Checking scrcpy...
scrcpy --version || (echo scrcpy not found in PATH & pause & exit)
echo Starting web-scrcpy...
cd /d %~dp0web-scrcpy
pip install -r requirements.txt
python app.py
pause
```

**Требования к окружению хоста:**
- Python 3.11+
- ADB в PATH (`winget install Google.PlatformTools`)
- scrcpy в PATH (`winget install Genymobile.scrcpy`)
- USB debugging включён на устройствах

---

## 6. Часть B — Card Management Panel

### 6.1 FastAPI — Onion-архитектура

**Принцип слоёв:**

```
HTTP Request
    ↓
Router (api/v1/*.py)        — валидация входных данных (Pydantic schemas)
    ↓
Service (services/*.py)     — бизнес-логика, оркестрация
    ↓
Repository (repositories/)  — SQL-запросы через SQLAlchemy
    ↓
Database (PostgreSQL)
```

**Пример: добавление карты**
```
POST /api/v1/cards
  → CardRouter.create_card(data: CardCreate)
    → CardService.create(data) — валидация бизнес-правил
      → CardRepository.insert(card_model) — INSERT в БД
        → return CardResponse
```

**Dependency Injection через FastAPI Depends:**
- `get_db_session` — async SQLAlchemy сессия
- `get_redis` — aioredis клиент
- `get_card_service` — инициализация с репозиторием

### 6.2 React-панель — дизайн PyCharm Island

**Цветовая схема (CSS переменные):**
```css
--bg-primary:    #1E1F22;   /* основной фон */
--bg-secondary:  #2B2D30;   /* фон карточек, таблиц */
--bg-hover:      #35373B;   /* hover строк таблицы */
--accent:        #4D9CF8;   /* кнопки, выделение, ссылки */
--accent-hover:  #3D8CE8;
--text-primary:  #BCBEC4;   /* основной текст */
--text-muted:    #7A7E85;   /* вторичный текст, placeholder */
--border:        #393B40;   /* разделители */
--success:       #57965C;   /* статус online, доход */
--danger:        #CC4433;   /* ошибки, расход, блокировка */
--warning:       #D4A843;   /* предупреждения, busy */
```

**Шрифты:**
- Данные/код: `JetBrains Mono` (номера карт, ID устройств)
- UI: `Inter` или системный sans-serif

**Структура интерфейса:**
```
┌─────────────────────────────────────────────┐
│  [💳 Карты] [📊 Транзакции] [📱 Устройства] │  ← табы
├─────────────────────────────────────────────┤
│                                    [⚙ Настройки] │
│                                             │
│              Контент таба                   │
│                                             │
└─────────────────────────────────────────────┘
```

### 6.3 Таб "Карты"

**Таблица — Phase 1 поля (собираем сейчас):**

| Поле | Тип БД | Отображение |
|------|--------|-------------|
| `id` | UUID PK | скрыто |
| `full_name` | VARCHAR(255) | ФИО |
| `bank` | VARCHAR(100) | Банк |
| `card_number` | VARCHAR(20) | `**** **** **** 1234` (маска) |
| `card_last4` | VARCHAR(4) | для поиска по транзакциям |
| `phone_number` | VARCHAR(20) | Телефон |
| `purchase_date` | DATE | Дата покупки |
| `group_name` | VARCHAR(100) | Группа (заглушка) |
| `created_at` | TIMESTAMP | Добавлена |

**Таблица — Phase 2 поля (добавить через Alembic миграцию):**
- `balance` DECIMAL(15,2)
- `monthly_turnover` DECIMAL(15,2)
- `user_id` UUID (заглушка)
- `is_blocked` BOOLEAN DEFAULT FALSE
- `blocked_at` TIMESTAMP
- `unblocked_at` TIMESTAMP
- `link` TEXT

**Функциональность:**
- Таблица с пагинацией: 50 записей/страницу
- Поиск (debounce 300ms): по ФИО, банку, последним 4 цифрам карты
- Фильтр: по банку, группе
- Кнопка "+ Добавить карту" → модальное окно с формой
- Клик по строке → боковая панель с транзакциями этой карты

**Acceptance criteria:**
- Номер карты хранится полностью, отображается только маска `**** **** **** XXXX`
- Валидация при добавлении: номер карты 16 цифр, телефон в формате +7XXXXXXXXXX
- Поиск работает без перезагрузки страницы

### 6.4 Таб "Транзакции"

**Phase 1:** таблица пустая, структура готова  
**Phase 2:** заполняется из Telegram  
**Phase 3:** дополняется из ADB  

**Поля таблицы:**

| Поле | Тип БД | Описание |
|------|--------|----------|
| `id` | UUID PK | |
| `card_id` | UUID FK → cards | NULL если карта не определена |
| `amount` | DECIMAL(15,2) | сумма |
| `currency` | VARCHAR(10) | KZT, RUB, USD… |
| `direction` | ENUM(income, outcome) | |
| `merchant` | TEXT | получатель/отправитель |
| `transaction_date` | TIMESTAMP | дата из уведомления |
| `source` | ENUM(sms, pdf, adb, manual) | источник |
| `raw_text` | TEXT | исходное сообщение |
| `needs_review` | BOOLEAN DEFAULT FALSE | не удалось сопоставить карту |
| `created_at` | TIMESTAMP | |

**Функциональность:**
- Фильтр по карте, периоду, типу (доход/расход), источнику
- Итоговые суммы под таблицей
- Экспорт в CSV
- Строки с `needs_review=true` подсвечены жёлтым

### 6.5 Таб "Устройства"

**Данные:** FastAPI запрашивает `adb devices` через subprocess + статусы из Redis.

**Поля таблицы:**

| Поле | Описание |
|------|----------|
| Device ID | серийный номер |
| Модель | `adb shell -s {id} getprop ro.product.model` |
| Статус | `online` / `offline` / `busy` (цветовые бейджи) |
| Сессия начата | время подключения из Redis |
| Действия | "Подключиться" → открывает `{device_domain}/{device_id}` в новой вкладке |
| | "Разорвать" (если busy) → DELETE Redis ключа |

**Acceptance criteria:**
- Список обновляется каждые 30 сек (polling с фронта)
- "Подключиться" использует домен из настроек (не хардкод)
- "Разорвать сессию" мгновенно освобождает устройство

### 6.6 Настройки (⚙)

Настройки хранятся в таблице `settings` (key-value) в PostgreSQL. Кэшируются в Redis с TTL 60 сек.

**Phase 1 настройки:**

| Ключ | Тип | По умолчанию | Описание |
|------|-----|-------------|----------|
| `inactivity_timeout` | integer | `10` | Таймаут неактивности scrcpy-сессии (минуты) |
| `device_domain` | string | `http://localhost` | Домен для доступа к устройствам |
| `bot_token` | string | `""` | Telegram Bot Token |
| `allowed_user_id` | string | `""` | Telegram User ID администратора |

**Phase 2 настройки (добавить):**

| Ключ | Описание |
|------|----------|
| `transactions_chat_id` | Chat ID откуда парсить транзакции |
| `gemini_api_key` | Ключ Gemini API |
| `gemini_model` | Модель (по умолч. `gemini-2.5-flash`) |

**Phase 3 настройки (добавить):**

| Ключ | Описание |
|------|----------|
| `adb_notification_interval` | Интервал опроса уведомлений ADB (сек) |
| `bank_package_names` | JSON-список package name банковских приложений |

**UI настроек:** форма с группировкой по фазам, кнопка "Сохранить" для каждой группы. Секретные поля (токены, ключи) — тип `password` с кнопкой "показать".

---

## 7. Telegram-бот

### 7.1 Phase 1 — Добавление карт

**Сценарий:**
1. Пользователь отправляет боту текст с данными карты (любой формат)
2. Бот отправляет текст в Gemini 2.5 Flash
3. Gemini возвращает JSON с распознанными полями
4. Бот показывает карточку подтверждения с inline-кнопками ✅ / ✏️
5. При подтверждении → `POST http://fastapi:8000/api/v1/cards` с данными
6. Бот сообщает об успехе

**Системный промпт Gemini (парсинг карты):**
```
Извлеки данные банковской карты из текста. Верни ТОЛЬКО JSON без пояснений:
{
  "full_name": "ФИО строкой или null",
  "bank": "название банка или null",
  "card_number": "только цифры без пробелов или null",
  "phone_number": "+7XXXXXXXXXX или null",
  "purchase_date": "YYYY-MM-DD или null",
  "group_name": null
}
Если данных недостаточно — верни поля как null, не придумывай.
```

**Карточка подтверждения (пример сообщения бота):**
```
📋 Проверь данные карты:

👤 ФИО: Иванов Иван Иванович
🏦 Банк: Сбербанк
💳 Карта: **** **** **** 9012
📱 Телефон: +79001234567
📅 Дата покупки: 15.01.2025
🗂 Группа: не указана

[✅ Подтвердить]  [✏️ Исправить]  [❌ Отмена]
```

**Acceptance criteria:**
- Бот принимает команды только от `allowed_user_id` из настроек
- Некорректный формат → бот просит прислать данные заново
- После подтверждения карта мгновенно появляется в веб-панели

### 7.2 Phase 2 — Парсинг транзакций из чата

**Конфигурация:** `transactions_chat_id` задаётся в настройках панели.

**Обработка текстовых сообщений (SMS-уведомления):**

Системный промпт Gemini:
```
Проанализируй банковское уведомление. Верни ТОЛЬКО JSON:
{
  "is_transaction": true/false,
  "amount": число или null,
  "currency": "KZT/RUB/USD или null",
  "direction": "income/outcome или null",
  "merchant": "название или null",
  "transaction_date": "ISO datetime или null",
  "card_last4": "4 цифры или null"
}
Если это реклама, промо или не финансовое уведомление — верни {"is_transaction": false}.
```

**Обработка PDF-файлов:**
1. Скачать PDF из Telegram
2. Извлечь текст через `pdfplumber`
3. Если текст пуст — использовать Gemini Vision (отправить страницы как изображения)
4. Отправить текст в Gemini с тем же промптом
5. Сохранить транзакцию с `source="pdf"`

**Сопоставление карты:**
- Поиск карты по `card_last4` в PostgreSQL
- Если найдена одна → привязать `card_id`
- Если найдено несколько → сохранить с `needs_review=True`
- Если не найдена → сохранить с `card_id=NULL`, `needs_review=True`

**Дедупликация:** проверка по (transaction_date, amount, card_id) перед INSERT.

### 7.3 Phase 3 — Парсинг с ADB-устройств

**Механизм:**
```python
# Периодически (интервал из настроек)
adb shell -s {device_id} dumpsys notification
```

**Фильтрация:**
- Оставлять уведомления только от package names из `bank_package_names` (настройка)
- Отправлять текст уведомления в Gemini с промптом классификации транзакций
- `is_transaction: false` → пропустить, не сохранять
- `is_transaction: true` → сохранить с `source="adb"`

**Acceptance criteria:**
- Рекламные уведомления и банковские "истории" не создают записей
- Один и тот же `device_id` не опрашивается параллельно (mutex через Redis)

---

## 8. Модель данных

### 8.1 PostgreSQL схема

```sql
-- Карты
CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    bank VARCHAR(100),
    card_number VARCHAR(20) NOT NULL,
    card_last4 VARCHAR(4) NOT NULL,
    phone_number VARCHAR(20),
    purchase_date DATE,
    group_name VARCHAR(100),
    -- Phase 2 (добавить через Alembic):
    -- balance DECIMAL(15,2),
    -- monthly_turnover DECIMAL(15,2),
    -- user_id UUID,
    -- is_blocked BOOLEAN DEFAULT FALSE,
    -- blocked_at TIMESTAMP,
    -- unblocked_at TIMESTAMP,
    -- link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Транзакции
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID REFERENCES cards(id) ON DELETE SET NULL,
    amount DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'KZT',
    direction VARCHAR(10) CHECK (direction IN ('income', 'outcome')),
    merchant TEXT,
    transaction_date TIMESTAMP WITH TIME ZONE,
    source VARCHAR(10) CHECK (source IN ('sms', 'pdf', 'adb', 'manual')),
    raw_text TEXT,
    needs_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (transaction_date, amount, card_id)  -- дедупликация
);

-- Настройки
CREATE TABLE settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Начальные данные
INSERT INTO settings (key, value) VALUES
    ('inactivity_timeout', '10'),
    ('device_domain', 'http://localhost'),
    ('bot_token', ''),
    ('allowed_user_id', '');
```

### 8.2 Redis-ключи

| Ключ | Значение | TTL |
|------|---------|-----|
| `session:lock:{device_id}` | `{"session_id":"uuid","connected_at":"ISO"}` | `inactivity_timeout * 60` сек |
| `settings:cache:{key}` | значение настройки | 60 сек |
| `adb:mutex:{device_id}` | `"1"` | `adb_notification_interval` сек |

---

## 9. API эндпоинты (FastAPI)

### Cards
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/cards` | Список карт (query: `search`, `bank`, `group`, `page`, `limit`) |
| POST | `/api/v1/cards` | Создать карту |
| GET | `/api/v1/cards/{id}` | Детали карты |
| PUT | `/api/v1/cards/{id}` | Обновить карту |
| DELETE | `/api/v1/cards/{id}` | Удалить карту |
| GET | `/api/v1/cards/{id}/transactions` | Транзакции карты |

### Transactions
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/transactions` | Все транзакции (фильтры: `card_id`, `source`, `direction`, `date_from`, `date_to`, `needs_review`) |
| POST | `/api/v1/transactions` | Создать вручную |
| PATCH | `/api/v1/transactions/{id}/review` | Отметить как проверенную |

### Devices
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/devices` | Список ADB устройств + Redis статусы |
| DELETE | `/api/v1/devices/{device_id}/session` | Принудительно снять сессию |

### Settings
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/settings` | Все настройки |
| GET | `/api/v1/settings/{key}` | Одна настройка (используется device.html) |
| PUT | `/api/v1/settings/{key}` | Обновить настройку |
| PUT | `/api/v1/settings` | Bulk update (несколько настроек сразу) |

---

## 10. Docker Compose

```yaml
# docker-compose.yml (схематично)

services:
  postgres:
    image: postgres:15-alpine
    env_file: .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks: [internal]

  redis:
    image: redis:7-alpine
    networks: [internal]

  backend:
    build: ./backend
    env_file: .env
    ports:
      - "127.0.0.1:8000:8000"   # только localhost
    depends_on: [postgres, redis]
    networks: [internal]
    extra_hosts:
      - "host.docker.internal:host-gateway"  # для обращения к хосту (опционально)

  frontend:
    build: ./frontend
    ports:
      - "127.0.0.1:3000:3000"   # только localhost
    networks: [internal]

  telegram-bot:
    build: ./telegram-bot
    env_file: .env
    depends_on: [backend]
    networks: [internal]

  nginx:
    image: nginx:alpine
    ports:
      - "0.0.0.0:80:80"         # публично — только для web-scrcpy
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks: [internal]

volumes:
  postgres_data:

networks:
  internal:
    driver: bridge
```

**nginx.conf (схематично):**
```nginx
server {
    listen 80;
    server_name _;  # или конкретный домен из настроек

    # web-scrcpy на хосте Windows
    location / {
        proxy_pass http://host.docker.internal:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";  # для WebSocket
        proxy_set_header Host $host;
    }
}
```

---

## 11. .env файл

```env
# PostgreSQL
POSTGRES_DB=cardpanel
POSTGRES_USER=carduser
POSTGRES_PASSWORD=changeme
DATABASE_URL=postgresql+asyncpg://carduser:changeme@postgres:5432/cardpanel

# Redis
REDIS_URL=redis://redis:6379/0

# Web-Scrcpy (хост)
SCRCPY_HOST_PORT=5000

# Telegram (Phase 1)
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USER_ID=

# Gemini (Phase 2)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

# Telegram парсинг (Phase 2)
TRANSACTIONS_CHAT_ID=

# ADB парсинг (Phase 3)
ADB_NOTIFICATION_INTERVAL=30
BANK_PACKAGE_NAMES=["com.sberbank.android","kz.homebank"]
```

---

## 12. Этапы разработки

### Phase 1 — Основа (добавление карт + устройства)

**Phase 1A: Инфраструктура**
- [ ] Настройка docker-compose (postgres, redis, backend, frontend, nginx, bot)
- [ ] `.env` + `pydantic-settings` в backend
- [ ] SQLAlchemy async engine + Alembic
- [ ] Начальная миграция: таблицы `cards`, `settings`

**Phase 1B: FastAPI Backend (Cards + Settings)**
- [ ] Onion-архитектура: models → repositories → services → routers
- [ ] CRUD для карт (`/api/v1/cards`)
- [ ] CRUD для настроек (`/api/v1/settings`)
- [ ] Устройства: `GET /api/v1/devices` (ADB + Redis статусы)
- [ ] `DELETE /api/v1/devices/{id}/session`

**Phase 1C: React Frontend**
- [ ] Vite + React проект, PyCharm Island CSS-тема
- [ ] Три таба: Карты, Транзакции (пустая), Устройства
- [ ] Таб "Карты": таблица, поиск, фильтры, модальное добавление
- [ ] Таб "Устройства": таблица, polling 30 сек, кнопка "Подключиться" → `{device_domain}/{device_id}`
- [ ] Панель настроек: inactivity_timeout, device_domain, bot_token, allowed_user_id

**Phase 1D: Telegram-бот (добавление карт)**
- [ ] aiogram 3, Polling
- [ ] Авторизация по `allowed_user_id`
- [ ] Хендлер текстовых сообщений → Gemini → карточка подтверждения
- [ ] POST в FastAPI при подтверждении

**Phase 1E: Web-Scrcpy (модификация)**
- [ ] Форк, `device_manager.py` — multi-device
- [ ] `session_manager.py` — Redis-блокировки
- [ ] Маршрутизация `/<device_id>`
- [ ] `device.html` — inactivity-таймер с загрузкой из FastAPI
- [ ] `start-scrcpy.bat`
- [ ] nginx проксирует Flask на 80 порт

---

### Phase 2 — Парсинг сообщений

- [ ] Добавление настроек Phase 2 в панель: `transactions_chat_id`, `gemini_api_key`, `gemini_model`
- [ ] Alembic миграция: таблица `transactions`
- [ ] FastAPI CRUD для транзакций
- [ ] React: Таб "Транзакции" — таблица, фильтры, CSV-экспорт, подсветка `needs_review`
- [ ] Telegram-бот: хендлер сообщений из `transactions_chat_id`
  - [ ] Парсинг текстовых SMS-уведомлений через Gemini
  - [ ] Парсинг PDF через `pdfplumber` + Gemini
  - [ ] Сопоставление с картой по `card_last4`
  - [ ] Дедупликация транзакций
- [ ] Alembic миграция: Phase 2 поля карт (balance, is_blocked и др.)

---

### Phase 3 — Парсинг с ADB-устройств

- [ ] Добавление настроек Phase 3: `adb_notification_interval`, `bank_package_names`
- [ ] Сервис опроса ADB-уведомлений (`dumpsys notification`)
- [ ] Фильтрация по package names
- [ ] Классификация через Gemini (транзакция vs реклама)
- [ ] Redis mutex на опрос устройства
- [ ] Сохранение с `source="adb"`

---

## 13. Потенциальные проблемы и решения

| Проблема | Решение |
|---------|---------|
| Docker Desktop + USB на Windows — WebSocket нестабилен через host.docker.internal | nginx использует `proxy_set_header Upgrade` для WS; тестировать с реальным доменом |
| scrcpy-процесс зависает на Windows | Watchdog-таймер в `device_manager.py`: если процесс жив >5 мин без активности — kill |
| Gemini неверно классифицирует рекламу как транзакцию | `needs_review=True` для низкой уверенности; ручная проверка в панели |
| PDF с нечитаемым текстом (скан) | Fallback: конвертировать страницы в PNG, отправить в Gemini Vision |
| Redis недоступен при старте web-scrcpy | Graceful fallback: InMemory dict с предупреждением в логах |
| ADB теряет устройство при переподключении | Polling каждые 30 сек + auto-restart процесса scrcpy |
| Дублирование транзакций при перезапуске бота | UNIQUE constraint в БД + обработка IntegrityError в репозитории |
| Telegram Polling — задержка доставки | Приемлемо для данного use-case; Webhook требует HTTPS-домена |

---

## 14. Безопасность

- FastAPI (`localhost:8000`) и React (`localhost:3000`) **не открываются наружу** — только через `127.0.0.1` в docker-compose
- nginx открыт публично **только для web-scrcpy** (порт 80)
- Токены и API-ключи — только в `.env`, добавить в `.gitignore`
- Telegram-бот принимает команды **только от** `allowed_user_id`
- Настройки с секретами (`bot_token`, `gemini_api_key`) — поля типа `password` в UI

---

## 15. Зависимости (requirements.txt)

**backend:**
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
redis[asyncio]>=5.0.0
pydantic-settings>=2.0.0
```

**telegram-bot:**
```
aiogram>=3.4.0
pydantic-settings>=2.0.0
google-generativeai>=0.5.0   # Gemini SDK
pdfplumber>=0.10.0            # Phase 2
httpx>=0.27.0                 # POST в FastAPI
```

**web-scrcpy (хост):**
```
flask>=3.0.0
redis>=5.0.0
```

---

## 16. Возможности будущего расширения

- Авторизация в панели (JWT) — если потребуется командный доступ
- WebSocket в React — real-time обновление транзакций без polling
- Статистика и графики — обороты по дням, разбивка по банкам
- История сессий устройств — лог подключений с временными метками
- Экспорт карт в Excel
- Уведомления в Telegram — алерты о новых транзакциях или событиях устройств
