# Mentor System Setup Instructions

## 1. Run Supabase Migration

You need to run the migration to create the mentor tables in your Supabase database.

### Option A: Using Supabase CLI (Recommended)
```bash
cd /home/kelly_koome/Devops/wealthcraft-legacy-sim
supabase db push
```

### Option B: Using psql with your Supabase connection string
```bash
# Replace with your actual Supabase connection string from .env
psql "postgresql://postgres.lllydwymcuulrsqxumvl:[YOUR_PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres" -f supabase/migrations/20250126_create_mentor_tables.sql
```

### Option C: Using Supabase Dashboard
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to SQL Editor
4. Copy the contents of `supabase/migrations/20250126_create_mentor_tables.sql`
5. Paste and run

## 2. Seed Mentor Data

After creating the tables, seed the mentor data:

### Using psql:
```bash
psql "postgresql://postgres.lllydwymcuulrsqxumvl:[YOUR_PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres" -f my_flask_app/seed_mentors.sql
```

### Using Supabase Dashboard:
1. Go to SQL Editor
2. Copy contents of `my_flask_app/seed_mentors.sql`
3. Paste and run

## 3. Setup Scheduled Job

### Option A: Using cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * cd /home/kelly_koome/Devops/wealthcraft-legacy-sim/my_flask_app && /usr/bin/python3 jobs/daily_mentor_analysis.py >> logs/mentor_analysis.log 2>&1
```

### Option B: Using systemd timer (Linux)
Create a systemd service and timer for more reliable scheduling.

### Option C: Using Supabase Edge Functions (Recommended for production)
Deploy the mentor analysis as a Supabase Edge Function with scheduled trigger.

## 4. Test the System

### Manual test:
```bash
cd /home/kelly_koome/Devops/wealthcraft-legacy-sim/my_flask_app
python3 jobs/daily_mentor_analysis.py
```

### Check logs:
```bash
tail -f logs/mentor_analysis.log
```

## 5. Verify in Mobile App

1. Open the mobile app
2. Navigate to Mentors screen
3. You should see 3 mentors (Coach Chen, Tasha, Your Parent)
4. Messages will appear based on your financial data

## Tables Created

- `mentors` - 3 mentor NPCs
- `mentor_messages` - 12 message templates (4 per mentor)
- `player_mentor_interactions` - Player message history

## Message Triggers

**Coach Chen (Strategic):**
- High cash ratio (>50%)
- Poor diversification (>70% in one asset)
- Net worth growth (+20%)
- Overextension (liabilities >40%)

**Tasha (Risk Analyst):**
- High debt-to-income (>40%)
- Low passive income (<20%)
- High expense ratio (>80%)
- Negative cash flow

**Your Parent (Emotional):**
- First $10K milestone
- Expensive purchases
- 7+ days inactivity
- Financial stress (negative net worth)

## Troubleshooting

**Migration fails:**
- Check your DATABASE_URL in .env
- Ensure you have the correct Supabase password
- Try using Supabase Dashboard SQL Editor

**Scheduled job not running:**
- Check cron logs: `grep CRON /var/log/syslog`
- Verify Python path: `which python3`
- Check file permissions: `chmod +x jobs/daily_mentor_analysis.py`

**No messages appearing:**
- Run manual test to check for errors
- Verify seed data was inserted: `SELECT COUNT(*) FROM mentors;`
- Check player financial data exists
