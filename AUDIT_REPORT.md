# Adulting / Wealthcraft — Audit Report (2026-11-20)

Scope: `Wealthcraft-backend` (Flask API, `main`) and `adulting` (Expo app on the **`dev`** branch;
`main` of that repo is an older Vite/Capacitor web app).

Everything listed under **Fixed** is in the working tree of both repos, **uncommitted**, so you can
review the diff before committing.

---

## 1. Recreating the database

1. Create the new Supabase project.
2. SQL Editor: run, in order,
   1. `supabase/schema.sql`: all 40 tables, FKs, indexes, RLS, auth trigger, money functions, realtime, avatars bucket
   2. `supabase/seed.sql`: **starter** catalogue (assets, jobs, courses, rentals, lifestyle items, bank-loan products, 2 missions)
   3. `my_flask_app/seed_mentors.sql`, then `my_flask_app/seed_life_events.sql`
   4. `supabase/cron.sql`, after enabling `pg_cron` + `pg_net` and adding the two Vault secrets it describes
3. **Authentication → Providers → Google**: enable it and add your Web client ID (plus the Android client ID).
   The app now signs in with `supabase.auth.signInWithIdToken`.
4. Backend env: see `.env.example`. New projects issue `sb_publishable_…` / `sb_secret_…` keys and sign JWTs
   with ES256. The backend now verifies tokens via JWKS, so `SUPABASE_JWT_SECRET` is only needed for legacy projects.
5. App env: `EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_ANON_KEY` (publishable key), `EXPO_PUBLIC_API_URL`.
6. Admin (for `/api/balance/add`):
   `update auth.users set raw_app_meta_data = raw_app_meta_data || '{"role":"admin"}' where email = '…';`
7. **Do not deploy the old Edge Functions** in `adulting/supabase/functions`. They duplicate the Flask cron jobs
   (loans/rent would be charged twice), and `daily-volatility` writes prices with the *anon* key.

Why a new schema instead of the old migrations: `adulting/supabase/migrations` cannot be replayed. The first
migration has a syntax error (trailing comma in `CREATE TABLE profiles`). The migrations are also missing
`void_posts`, `void_reactions`, `market_news`, `ai_response_cache`, `profiles.sanity`,
`profiles.expo_push_token`, `get_top_players` and more; the live DB had been edited by hand. Their RLS also let
players `UPDATE` their own `user_balances` directly from the app (free money). **None of the catalogue data
(assets, jobs, courses, rentals, lifestyle items, missions) was ever committed**, so `seed.sql` is a placeholder
set: tune the numbers.

Schema conventions now enforced:
- Every player column (`user_id` / `player_id`) holds `auth.users.id` and FKs to `profiles(user_id)`. This
  removes the "auth uid vs profile id" ambiguity the 9 copies of `resolve_user_ids()` were working around.
- Money moves only through `adjust_balance()`: atomic, never overdraws, always writes a transaction.
- New players get a profile and **$5,000 starting cash** (constant in `handle_new_user`). Username collisions
  get a suffix instead of failing sign-up with a 500.
- Players can read public profile stats but cannot read anyone's push token, and can only write their own
  `expo_push_token`. They cannot touch balances, net worth, sanity or credit score.

---

## 2. Fixed: critical

| # | Problem | Where | Fix |
|---|---|---|---|
| 1 | After any `/api/auth/login` or `/register`, the **shared service-role Supabase client switched its Authorization header to that user's token** (supabase-py behaviour on `SIGNED_IN`). Every later query in that worker ran as the last user who logged in, under RLS. | `services/user_service.py` | Auth calls use a throwaway anon client |
| 2 | `require_admin` trusted `user_metadata.role`, which **any user can set** via `supabase.auth.updateUser`. That gives unlimited money via `/api/balance/add`. | `utils/jwt_helper.py` | Uses `app_metadata` |
| 3 | `PUT /api/profile/<id>/` and `POST /api/profile/` had **no auth**, and the schema accepted `net_worth`, `monthly_income`, `credit_score`. Anyone could edit anyone's leaderboard stats. | `routes/profile_routes.py`, `schemas/profile_schema.py` | Auth + own-profile only + cosmetic fields only |
| 4 | **Job farming**: hiring paid the *full annual salary* as cash; quit → re-apply repeated it forever. | `routes/job_routes.py` | One-time signing bonus = 1 month's pay, once per listing |
| 5 | **Negative loan repayment** (`amount: -1000000`) *added* cash and grew the lender's P2P debt. | `routes/loan_routes.py` | Amount must be > 0 |
| 6 | **Life-event replay**: payout happened even when the event was already answered or never assigned, and the choice wasn't checked against the event (pick the richest choice from any event). | `routes/life_event_routes.py` | Choice must belong to event; atomic claim must update a pending row |
| 7 | **Course completion replay**: each call re-added the permanent salary boost and the 2× bonus; completion was also allowed instantly. | `routes/education_routes.py` | Atomic once-only claim + `duration_hours` must elapse |
| 8 | **Mission story events** paid `immediate_cash` on every acknowledge. | `routes/mission_routes.py` | Paid once |
| 9 | **Read-modify-write balances**: concurrent requests lost updates and allowed double-spend; `subtract_balance` accepted negative amounts. | `services/balance_service.py` | `adjust_balance` RPC |
| 10 | **Double-sell races**: asset and lifestyle sales paid out before removing the item, so two parallel requests both got paid. | `routes/asset_routes.py`, `services/liability_service.py` | Claim the row atomically, then pay |
| 11 | **Google sign-in could never work**: Flask minted its own HS256 JWT for a separate `public.users` table; Supabase rejects sessions for users not in `auth.users`. | `app/auth.tsx`, backend | Client uses `signInWithIdToken`; endpoint, `User` model and service deleted |
| 12 | Backend verified only HS256 with the legacy secret. **New Supabase projects sign with ES256**, so every request would be 401 on the new project. | `utils/jwt_helper.py` | JWKS (ES256/RS256) + HS256 fallback; tested |
| 13 | `my_flask_app/.env` (real secrets) and the 886 MB gcloud SDK were copied into the Docker image (`.dockerignore` patterns are root-anchored). | `.dockerignore`, `.gcloudignore` | Excluded |
| 14 | Root `run.py` printed the first 50 chars of `DATABASE_URL` (includes the DB password) to logs. | `run.py` | Removed |

## 3. Fixed: high / gameplay logic

- **No salary was ever paid monthly.** The monthly job charged living costs (20% of income) but never paid
  income. It now runs a payday step: salaries/12 + permanent boosts.
- **Missions could never finish.** Nothing advanced `current_month` or wrote `mission_completion_results`. The
  monthly job now advances missions, evaluates criteria (net worth / income / credit score), pays
  `completion_reward` and notifies. The unique `(player_id, mission_id)` prevented retrying an abandoned
  mission; it's now "one *active* mission per player".
- **Credit score never changed anywhere.** It now goes +2 for on-time loan payments and −25 for missed ones,
  and missed payments add a 5% late fee. Before, the penalty was computed and discarded.
- **Bank loans were interest-free** (`remaining_balance` = principal only). Interest is now included, the
  `credit_required` score is enforced, you need a real loan template (not any loan row), loans are capped at
  3 active, and the `bank_loans` row is marked completed on payoff. The final instalment no longer overcharges.
- **Net worth was wrong both ways.** Lifestyle items you own were *subtracted* (a $10k watch cost $20k of net
  worth), and loans were ignored (borrowing raised your rank). Fixed in `ProfileService.recalculate_net_worth`;
  net worth is also recalculated after buys and sells.
- **P2P**: two borrowers could accept the same offer (now an atomic claim); there was no validation on rate
  or term (term 0 crashed accept); escrowed cash was stuck forever (added `POST /api/loans/p2p/cancel/`;
  the app still needs a button).
- **Void sanity farming**: un-react/re-react "same" gave +1 to both users every time. Sanity is now the
  difference between old and new reaction, and counters are recomputed in SQL.
- **Selling assets from the app was broken**: the app posts `/api/assets/sell/` with a body and the backend
  only had `/sell/<id>/`. Both now work, with partial-quantity sells. Fractional purchases were truncated by
  `int()` (0.5 BTC = free 0-quantity asset). Followers were notified twice per sale.
- **Course completion was unreachable**: the app sent `course_id` (backend expected `user_course_id`), and the
  only caller was an unused component. Added a "Claim Certificate" button when the timer reaches 100%.
- **Referral "hustle" bonus charged the new player $1,000** (it called the paid `vacation` recovery). The
  "nepo" bonus called the admin-only endpoint (always 403). Both removed; it needs a server-side claim endpoint.
- **Lifestyle purchases from the app** used a second, buggy code path (no `current_value`, so the item vanished
  from net worth and resale). Now aliased to the main purchase.
- Monthly jobs are **idempotent** (`cron_runs` table), so a retry can no longer double-charge rent and loans.
- `/api/liabilities/cron/monthly-depreciation` was **unauthenticated** (anyone could depreciate everyone
  repeatedly). Removed; `/api/cron/depreciation/` already exists behind `CRON_SECRET`.
- `/api/social/search/` was public and returned `select('*')` of profiles, **including push tokens**. Now
  authed, limited columns, wildcard-escaped.
- `from gotrue.errors import AuthApiError` caught the wrong class (supabase-py raises
  `supabase_auth.errors.AuthApiError`), so a wrong password returned **500** instead of 401.
- `models/__init__.py` listed a non-existent `FamilyMember` in `__all__` (`import *` crashed).
- Production silently fell back to `sqlite:///app.db` when `DATABASE_URL` was missing. It now fails fast.
- Market news never had a `category`, so every per-screen "news" panel was empty. Generated news is now `market`.
- Push taps to `/loans` and `/profile/<id>` hit non-existent routes (now `/banking`, `/profile?id=`).
- `useAuth` re-registered the push token on every hourly token refresh.
- Cron secret comparison is now constant-time.

---

## 4. Found, NOT fixed (need your decision or a bigger change)

**Backend**
- **Background threads on Cloud Run**: follower pushes and the 4-hourly market job run in `threading.Thread`
  after the response returns. With default (request-based) CPU allocation, Cloud Run throttles the CPU once
  the response is sent. That is likely the cause of `PUSH_NOTIFICATION_DELAYS_ANALYSIS.md`. Deploy with
  `--no-cpu-throttling`, or run the work synchronously / via Cloud Tasks.
- **Mission constraints are not enforced server-side.** `can_buy_assets`, `can_take_loans` etc. are only
  checked by the app (`useMissionConstraints`). The buy/loan endpoints never call `check-constraints`. Mission
  decisions also aren't gated by month (you can answer month-6 decisions in month 1).
- **Two data layers on one DB**: SQLAlchemy (`DATABASE_URL`) for profiles, mentors, AI, leaderboard,
  liabilities; Supabase REST for everything else. Pick one. REST + RPCs fits Supabase best.
- `resolve_user_ids()` is copy-pasted into 9 route files (2 different implementations). With the new schema
  it's unnecessary; delete it once you're on the new DB.
- Many handlers still use `.single()` then `if not response.data: return 404`. `.single()` *raises* on 0 rows,
  so those 404 branches are dead and the client gets a 500.
- Free `touch_grass` (+5 sanity) has no cooldown, which makes sanity meaningless.
- Follower "student move" notifications are written to the in-app feed **only when the push fails**, so the
  notifications screen misses most of them.
- `POST /api/void/scream/` blocks on the LLM (30 s timeout) inside the request.
- Net worth isn't recalculated after appreciation, depreciation or market moves; the leaderboard lags until
  the player's next transaction.
- Not reviewed line-by-line: `mentor_service.py`, `ai_service.py`, `daily_mentor_analysis.py`,
  `inactive_users_monitor.py` (only their DB usage and wiring were checked).

**Frontend (`adulting/Adulting`)**
- Native Notify is dead weight: the backend now sends via Expo directly, yet `_layout.tsx` still calls
  `registerNNPushToken(33561, '…token…')` on every render with the token hard-coded (also in `nativeNotifyHelper.ts`).
- P2P "cancel offer" button (endpoint added) and a server-side referral claim are missing.
- Email login and sign-up proxy through Flask just to call Supabase. Calling `supabase.auth.signInWithPassword`
  directly from the app would be simpler.

**Tests**
- `my_flask_app/tests` never ran: `db.create_all()` on SQLite can't compile the Postgres `ARRAY`/`JSONB`
  columns (13 errors at setup). The `test_*.py` files beside the app are manual scripts that hit live services.

---

## 5. Dead code

Deleted in this pass:
- **Backend**: `services/google_auth_service.py`, `services/asset_service.py`, `utils/supabase_client.py`
  (never imported; it would also crash on import without env vars), `utils/mentor_constraint_filter.py`,
  models `User`, `LoanRepayment`, `MonthlyDeduction` (only used to delete rows nothing wrote),
  `IntegratedMissionEvent`, `MissionEventChoice`, `MissionCourse`, `MissionAsset`, `create_token()`,
  `/google-signin/`.
- **Frontend**: `hooks/useLifeEvents.tsx` (had a syntax error that stopped `tsc` from type-checking the whole
  app), `components/modals/LifeEventModal.tsx`, the dead `api.auth.googleSignIn`, `api.balance.add`,
  `api.liabilities.takeLoan` / `payLoan`.

Still present, never imported (safe to delete):
- `components/`: `banking/LoanCard`, `banking/TransactionList`, `dashboard/LiabilitiesList`,
  `education/CourseCard`, `lifestyle/LifestyleCard` (also has a type error), `market/AssetCard`,
  `market/CategoryFilter`, `profile/FollowStats`, `profile/MyHomeCard`, the Expo template leftovers
  (`external-link`, `haptic-tab`, `hello-wave`, `parallax-scroll-view`, `ui/collapsible`)
- `lib/notificationApi.ts`, `lib/secureStorage.ts`, `hooks/index.ts` (barrel nobody imports),
  `types/native-notify.d.ts`, `app.json.backup`
- **Backend**: `lambda_handler.py`, `template.yaml`, `install_aws_tools.sh` and the Lambda docs (you deploy
  to Cloud Run); `apig-wsgi` in requirements; the deprecated `gotrue` package; one-off scripts
  (`analyze_supabase_connection.py`, `check_password_encoding.py`, `connection_guide.py`, `diagnose_db_url.py`,
  `fix_python38_compat.py`, `inspect_*.py`, `reproduce_issue.py`, `verify_*.py`, `scratch/`); unused Pydantic
  response schemas (`UserResponse` even declares `id: int` for a UUID).

---

## 6. Repository hygiene

- **Both repos track the entire Google Cloud SDK** (~7,100 files, 886 MB on disk) in a folder literally named
  `my_flask_app/exec -l /bin/bash\rgcloud --version`, created by a mistyped command. The backend also tracks
  `venv/` (Python 3.8) and `.venv/` (Python 3.11) and ten empty files named `--cpu`, `--image`, … from a broken
  multi-line `gcloud` command. `.gitignore` is updated; untrack them with:
  ```bash
  git rm -r -q --cached "my_flask_app/exec -l /bin/bash"$'\r'"gcloud --version" venv .venv
  git rm -q -- --allow-unauthenticated --cpu --image --max-instances --memory --platform --region --set-env-vars --set-secrets --timeout
  ```
  (History keeps them. Use `git filter-repo` if you want the repo size back.)
- The `adulting` `dev` branch holds **three projects**: the Expo app, the old Vite web app (`src/`,
  `index.html`, `vite.config.ts`…) and a **drifted copy of the whole Flask backend** (`adulting/my_flask_app`,
  also with the gcloud SDK). Delete the copy and the old web app; keep the backend only in `Wealthcraft-backend`.
- `adulting/my_flask_app/tests/test_supabase.py` contains a hard-coded **service-role key** (for the deleted
  project, so it no longer works, but remove it). Restrict the Google API key in `google-services.json` to your
  Android app in the Google Cloud console.
- Two `requirements.txt` and two `deploy.sh` files that have drifted apart; the Docker build uses the root
  `requirements.txt`. Docs still mention Gemini, Render and Lambda.
