# Adulting Flask backend

Flask API for the Adulting mobile app. Data lives in Supabase (Postgres); the
schema and all seed data are owned by `../supabase/`, not by this app.

## Layout

```
my_flask_app/
├── run.py              # app entry point (gunicorn run:app in Docker; python run.py locally)
├── config.py           # env-driven config (development / production / testing)
├── run_local.sh        # serve on your LAN so a phone can reach it
├── app/
│   ├── routes/         # HTTP endpoints, one blueprint per area
│   ├── services/       # business logic (balances, mentors, AI, push, ...)
│   ├── game/           # weekly game loop: cards, careers, homes, market, squads, ...
│   ├── models/         # SQLAlchemy models (mirrors of supabase/schema.sql tables)
│   ├── schemas/        # Pydantic request/response validation
│   └── utils/          # auth (JWT), DB helpers, mission constraints, caching
├── jobs/               # scheduled jobs, triggered via /api/cron/* (see ../supabase/cron.sql)
├── tests/              # automated pytest suite (offline)
└── scripts/            # manual tools against a real project (see scripts/README.md)
```

## Quick start

```bash
# from the repo root
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example my_flask_app/.env      # fill in Supabase URL/keys and DATABASE_URL

cd my_flask_app
../.venv/bin/python run.py --host 0.0.0.0     # http://localhost:5000
```

Database setup (once per Supabase project), all in `../supabase/`: run
`schema.sql`, then `seed.sql`, `seed_mentors.sql`, `seed_life_events.sql`, then
the files in `migrations/` in order, then `cron.sql`.

## Tests

```bash
cd my_flask_app
../.venv/bin/python -m pytest
```

## Deploy

Cloud Run via the root `Dockerfile` and `deploy.sh` (see `../docs/CLOUDRUN_DEPLOYMENT_GUIDE.md`).
The full endpoint list is in `../docs/FLASK_API_ENDPOINTS.md`.
