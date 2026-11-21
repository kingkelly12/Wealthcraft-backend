
---

## 7. Second pass (2026-11-21): mentors end-to-end + remaining logic

### Mentors (tested end-to-end on a local Postgres with the real schema + `seed_mentors.sql`)
| Problem | Fix |
|---|---|
| Chat history sorted oldest-first *then* limited to 20, so after 20 messages the chat screen and the AI's context were frozen on the first 20 | Latest N, returned oldest-first (`AIService.get_conversation_history`) |
| Daily mentor nudges were excluded from chat history. Tapping the push opened a chat that didn't show the message, and silently marked it read | History includes the mentor's nudges; their template CTA becomes a tappable action |
| Daily job had no cooldown and no once-per-day guard: the same top-2 nags were pushed to every player every day | Per-trigger cooldowns, one-time celebrations, max 1 message per mentor, `cron_runs` daily guard |
| Metrics fed the triggers wrong data: passive income hard-coded to 0 (`low_passive_income` fired for everyone); `income_sources_count`/`monthly_savings`/`engagement_days` never updated (`single_income_source` always on, savings/progress never); inactivity measured from `updated_at`, which every balance sync bumps; debt measured as original principal; buying an asset counted as "spending"; `first_asset`/`debt_free`/`milestone_10k` re-fired daily; `cash_ratio` = cash/assets (0 with no assets) | All computed from real data; non-operating transaction categories excluded |
| `overextension` compared debt to investments only ("1000% of your assets" for a cash-rich player) | Debt vs. everything owned |
| A template placeholder missing from the trigger data raised `KeyError` and, with no rollback, broke the run for every later player | Safe formatting per message + `rollback()` per player |
| Persona/rules were pasted into the *user* message (easy for chat text to override); model output (`relationship_points`, `suggested_actions`) was trusted as-is | System role + JSON mode; output normalised: points clamped 0–10, actions validated, tone whitelisted |
| "Follow advice" XP could be claimed on your own chat lines and twice via concurrent taps | Mentor messages only; atomic once-only claim |
| Cache TTL used `timedelta.seconds` (drops days) | `total_seconds()` |

**Your Qwen key returns `403: free quota exhausted`.** Every mentor chat, greeting, Void reply and market
headline currently uses the template fallbacks. Add billing in Alibaba Cloud Model Studio, or turn off
"use free tier only".

Dead mentor templates: `expensive_purchase` (real-time triggers are intentionally disabled in
`MentorService.check_real_time_triggers`) and `net_worth_growth` (no trigger produces it).

### Other logic fixed
- **Mission constraints are now enforced server-side** (`app/utils/mission_constraints.py`) on buy/sell
  assets, bank and P2P loans, job apply/quit, rent/move-out and lifestyle purchases.
- Mission decisions can't be made before their month or twice. Story events can't be acknowledged before
  they're due. Probability events use a deterministic roll per mission/month: refreshing used to re-roll,
  and probability 0 used to mean "always".
- Every `.single()` (14 places) replaced with `fetch_one()`. Missing rows now give 404s, not 500s.
- Rent, course enrolment and P2P offers claim the record *before* charging (and undo on failure), so a
  double tap can no longer take the money twice or lose it.
- Market job: the $1.00 price floor made sub-dollar assets jump 5× (now $0.01); `price_change` and
  `price_change_percent` were never written (now they are); it now runs synchronously so Cloud Run
  doesn't throttle it; one malformed AI headline no longer drops the rest.
- Business assets were stored as `stocks`, so they were neither market-priced nor appreciated. They're
  now `business` and appreciate monthly like property.
- Sanity: free "touch grass" is limited to once per 24 h (new column `profiles.last_free_recovery_at`);
  paid recovery is refused at 100 sanity; all sanity writes are atomic (`adjust_sanity`).
- Follower "student move" notifications always land in the in-app feed (before, only when the push failed).

### Not fixed (design decisions for you)
- Life events never expire: `time_limit_seconds` and `was_auto_selected` exist but nothing uses them.
- Chat messages have no rate limit.
- Unused Pydantic schemas: `UserResponse`, `MentorResponse`, `MentorInteractionResponse`,
  `MarkAdviceFollowedResponse`, `MentorStatsResponse`, `LoanApplicationResponse`,
  `LifeEventChoiceRequest`/`Response`, `AssetResponse`, `UserAssetResponse`.
- Routes that go through Supabase REST (PostgREST) were compile-checked and reviewed but not executed;
  only the SQLAlchemy paths (mentors, AI chat, liabilities service) ran against a real database.
