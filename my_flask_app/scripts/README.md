# Developer scripts

Diagnostics and manual checks. None of these are part of the deployed app
(they're excluded from Docker, gcloud and SAM uploads).

Run them from `my_flask_app/` as modules, so `from app import ...` and `.env`
loading work:

```sh
cd my_flask_app
python -m scripts.inspect_schema          # a diagnostic
python -m pytest scripts/test_missions_api.py   # a manual check
```

| Kind | Files |
|---|---|
| Database / Supabase diagnostics | `analyze_supabase_connection`, `check_password_encoding`, `connection_guide`, `diagnose_db_url`, `inspect_schema`, `inspect_loans_schema`, `verify_supabase_project` |
| Push notifications | `diagnose_push_notification`, `test_push_notification` |
| Gameplay triggers | `trigger_life_event_test`, `verify_sanity` |
| Manual API checks (several need a running server or real credentials) | `test_*.py`, `regression_test`, `test_regression_direct` |
| Local networking | `setup_wsl_port_forward.ps1` (WSL → Windows port forwarding for Flask) |

The automated test suite lives in `my_flask_app/tests/`.
