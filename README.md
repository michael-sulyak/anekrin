# Anekrin

[![Scrutinizer Code Quality](https://img.shields.io/scrutinizer/g/expert-m/anekrin.svg?style=flat)](https://scrutinizer-ci.com/g/expert-m/anekrin/?branch=master)
[![GitHub Issues](https://img.shields.io/github/issues/expert-m/anekrin.svg?style=flat)](https://github.com/expert-m/anekrin/issues)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://choosealicense.com/licenses/apache-2.0/)

Anekrin is a simple personal productivity tracker for Telegram:

- Create tasks with rewards (scores).
- Mark tasks as completed and track your daily score.
- Keep a 7‑day rolling “average” with a target of 100.
- Organize tasks with categories.
- Export/Import data as JSON.
- Visualize progress with a calendar heatmap.
- Adjust timezone and edit a specific “work date”.

Status: Proof of Concept (usable, evolving).

---

## Features

- Tasks and rewards
    - Create, edit (name, reward, category), delete.
    - Quick “Complete” with per‑day counters.
- Daily/weekly stats
    - Daily score and 7‑day rolling average (target 100).
    - “Bonus for tomorrow” when you exceed the target.
- Categories
    - Create, rename, delete; filter tasks by category.
- Data portability
    - Export tasks and work logs to JSON.
    - Import work logs from JSON.
- Visuals
    - Calendar heatmap images (PNG) per year.
- UX niceties
    - Per‑user sequential processing (no race conditions).
    - Throttling on heavy actions.
    - Timezone selection and “work date” override.
    - Sample tasks created for new users.

---

## Tech Stack

- Python 3, Aiogram
- PostgreSQL + asyncpg + Tortoise ORM (Aerich for migrations)
- Matplotlib, Pandas, Calmap (calendar heatmap)
- Aio‑Pika (MQ, optional), Sentry (optional)

---

## Quick Start

Prerequisites:

- Telegram Bot Token (create via @BotFather).
- Docker and Docker Compose (or Python 3 + PostgreSQL if running locally).

1) Copy and edit environment variables (example)

- File: envs/local.env
- Set at least:
    - POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
    - TELEGRAM_API_TOKEN
    - SENTRY_DSN (optional)
    - TELEHOOKS_MQ_URL, TELEHOOKS_MQ_QUEUE_NAME (optional)

2) Run with Docker

- docker compose up -d
- The bot will start and connect to PostgreSQL.
- Open your bot in Telegram and send /start.

Notes:

- First run will create sample tasks you can remove later.
- Settings → change timezone and choose dates for editing if needed.

---

## Local Development

1) Install deps

- poetry install

2) Start PostgreSQL and export envs

- Use envs/local.env (adapt values for your local DB).
- Example: export $(grep -v '^#' envs/local.env | xargs)

3) Initialize DB

- If using migrations:
    - aerich upgrade
- Or generate schema directly (development only):
    - The app can generate schemas on init if configured.

4) Run the bot

- python __main__.py

---

## Configuration (Environment Variables)

- POSTGRES_DB: database name
- POSTGRES_USER: database user
- POSTGRES_PASSWORD: database password
- POSTGRES_HOST: database host
- POSTGRES_PORT: database port
- TELEGRAM_API_TOKEN: bot token from @BotFather
- SENTRY_DSN: Sentry DSN (optional)
- TELEHOOKS_MQ_URL: MQ URL (optional)
- TELEHOOKS_MQ_QUEUE_NAME: MQ queue name (optional)

---

## Using the Bot

- /start
    - Greets, shows help, and suggests updating timezone.
- Tasks
    - “Tasks” button: list tasks, complete, edit, create, categorize.
- Stats
    - “Stats” button: shows daily score and 7‑day average.
    - “Calendar heatmap”: get a PNG with your annual progress.
- Settings
    - Choose work date, change timezone, import/export data.
- Import/Export
    - Export: JSON files for tasks and work logs.
    - Import: upload JSON with work logs (validated and size‑limited).

Tip:

- The 7‑day “average” is the sum of the last 7 days divided by 7. Aim for 100.

---

## Testing

- pytest (async tests supported via pytest‑asyncio).
- The test suite creates a separate test DB automatically.
- Ensure POSTGRES_DB ends with _test for safety.

Run:

- pytest

---

## Architecture (Short)

- Each bot instance processes updates sequentially per user (one queue per user).
- Minimal in‑memory state; PostgreSQL is the source of truth.

---

## Contributing

Issues and PRs are welcome. Keep changes small, focused, and covered by tests where possible.

---

## License

Apache License 2.0. See LICENSE for details.
