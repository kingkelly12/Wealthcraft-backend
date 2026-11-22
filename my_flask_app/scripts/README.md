# Developer scripts

Manual tools for working against a real Supabase project. None of these are
part of the deployed app (they're excluded from Docker and gcloud uploads).

Run them from `my_flask_app/` as modules, so `from app import ...` and `.env`
loading work:

```sh
cd my_flask_app
../.venv/bin/python -m scripts.diagnose_push_notification <username>
../.venv/bin/python -m scripts.trigger_life_event_test --username <username>
```

| File | What it's for |
|---|---|
| `diagnose_push_notification.py` | Checks a player's Expo push token, sends a test push and explains why delivery failed |
| `trigger_life_event_test.py` | Assigns a random life event to a player right now (instead of waiting for the cron job) |
| `setup_wsl_port_forward.ps1` | Windows/WSL port forwarding so a phone on your Wi-Fi can reach Flask (pairs with `../run_local.sh`) |

The automated test suite lives in `my_flask_app/tests/` (`pytest` from `my_flask_app/`).
