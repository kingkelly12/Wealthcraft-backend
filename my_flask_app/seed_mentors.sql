-- Insert 3 Mentors
INSERT INTO mentors (id, name, role, personality, avatar_url, greeting_template) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'Coach Chen',
  'strategic',
  'Direct, analytical, celebrates wins, provides tough love when needed. Focuses on portfolio strategy, asset allocation, and risk management.',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Chen',
  'Hey {username}, I''ve been watching your portfolio...'
),
(
  '22222222-2222-2222-2222-222222222222',
  'Financial Advisor Tasha',
  'risk_analyst',
  'Cautious but encouraging, questions risky moves, data-driven. Focuses on risk assessment, debt management, and income optimization.',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Tasha',
  'Hi {username}, let''s look at the numbers...'
),
(
  '33333333-3333-3333-3333-333333333333',
  'Your Parent',
  'emotional',
  'Warm, worried, proud, shares wisdom from experience. Focuses on life balance, emotional well-being, and long-term security.',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Parent',
  'Sweetheart...'
);

-- ============================================
-- COACH CHEN MESSAGE TEMPLATES (4)
-- ============================================

-- 1. High Cash Ratio
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'high_cash_ratio',
  'Hey {username}, you''re sitting on ${cash_amount:,} cash. That''s {cash_percentage}% of your net worth!

Inflation is eating ${inflation_loss:,} yearly. That''s money losing value while you sleep.

Action: Move at least 60% into dividend stocks or REITs. Keep 3-6 months expenses as emergency fund.

Remember: Cash is for safety, assets are for wealth. Let''s build both.',
  'View Investment Options',
  'navigate_to_marketplace',
  '{"cash_ratio_min": 0.5}',
  4,
  15,
  true
);

-- 2. Poor Diversification
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'poor_diversification',
  'Listen up {username}, {concentration}% of your portfolio is in one asset type. That''s dangerous.

If that sector crashes, you lose everything. Diversification isn''t just smart - it''s survival.

Action: Spread across at least 3 asset classes. Stocks, real estate, bonds - mix it up.

Don''t put all your eggs in one basket. Ever.',
  'Diversify Portfolio',
  'navigate_to_marketplace',
  '{"concentration_min": 0.7}',
  4,
  20,
  true
);

-- 3. Net Worth Milestone (Positive)
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'net_worth_growth',
  'Impressive, {username}! Your net worth jumped {growth_percentage}% to ${net_worth:,}.

That''s the power of compound growth. But don''t get cocky - this is where most people plateau.

Next level: Increase your income streams. One source of income is risky. Build 3-5.

Keep the momentum. You''re doing what 90% of people never do.',
  'View Progress',
  'navigate_to_profile',
  '{"net_worth_growth_min": 0.2}',
  3,
  15,
  true
);

-- 4. Overextension (Too Many Liabilities)
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'overextension',
  'Whoa {username}, you''re overextending. {liability_percentage}% of your assets are tied up in liabilities.

That''s a house of cards. One bad month and it all collapses.

Action: Sell non-essential liabilities. That fancy car? It''s costing you wealth. Consolidate and simplify.

Rich people buy assets. Broke people buy liabilities disguised as assets.',
  'Review Liabilities',
  'navigate_to_liabilities',
  '{"liability_ratio_min": 0.4}',
  5,
  25,
  true
);

-- ============================================
-- FINANCIAL ADVISOR TASHA MESSAGE TEMPLATES (4)
-- ============================================

-- 1. High Debt-to-Income
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '22222222-2222-2222-2222-222222222222',
  'high_debt_to_income',
  'Hi {username}, I''m concerned. Your debt payments are {debt_percentage}% of your income.

The rule of thumb is to keep it under 36%. You''re in the danger zone.

At this rate, you''ll be paying interest for years while your wealth stagnates.

Action: Create a debt payoff strategy. Pay off highest interest first. Consider consolidation.

Let''s get you free from this burden.',
  'Create Debt Plan',
  'navigate_to_loans',
  '{"debt_to_income_min": 0.4}',
  5,
  25,
  true
);

-- 2. Low Passive Income
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '22222222-2222-2222-2222-222222222222',
  'low_passive_income',
  'Hi {username}, I need to be blunt with you.

Your passive income is less than 20% of your total income. That means you''re trading time for money.

If you stop working, the money stops. That''s not financial freedom - that''s a job.

Action: Buy income-generating assets. Dividend stocks, rental properties, mutual and Index funds. Build streams that flow while you sleep.

Increase your passive income or you''ll work until you die.',
  'Find Income Assets',
  'navigate_to_marketplace',
  '{"passive_income_ratio_max": 0.2}',
  4,
  20,
  true
);

-- 3. High Expense Ratio
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '22222222-2222-2222-2222-222222222222',
  'high_expense_ratio',
  'Hi {username}, your expenses are {expense_percentage}% of your income.

You''re living paycheck to paycheck. There''s no room for savings, no room for investing.

Your rent/monthly expenses are very high in relation to your monthly income. You can move to a cheaper place, sell some liabilities, or increase your monthly income.

Action: Cut expenses by 20%. Track every dollar. Find the leaks.

You can''t build wealth if you''re spending it all.',
  'Review Budget',
  'navigate_to_profile',
  '{"expense_ratio_min": 0.8}',
  4,
  20,
  true
);

-- 4. Negative Cash Flow
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '22222222-2222-2222-2222-222222222222',
  'negative_cash_flow',
  'Hi {username}, red alert. Your expenses exceed your income by ${deficit:,}/month.

This is unsustainable. You''re going backwards financially.

Every month you''re digging a deeper hole. This ends in bankruptcy if not fixed immediately.

Action: Emergency budget cuts. Increase income. Sell assets if needed. Get cash flow positive NOW.

This is the most important financial metric. Fix it today.',
  'Emergency Budget',
  'navigate_to_profile',
  '{"cash_flow_max": 0}',
  5,
  30,
  true
);

-- ============================================
-- YOUR PARENT MESSAGE TEMPLATES (4)
-- ============================================

-- 1. First $10K Milestone
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '33333333-3333-3333-3333-333333333333',
  'milestone_10k',
  'Sweetheart, ${net_worth:,}! I''m so proud of you.

I remember when you started with nothing. Look at you now - building real wealth.

This is just the beginning. The first $100K is the hardest. Now momentum is on your side.

Keep going. You''re doing better than I did at your age.

Love you always,
Mom/Dad',
  'Share Achievement',
  'share_milestone',
  '{"net_worth_min": 10000, "net_worth_max": 15000}',
  3,
  10,
  true
);

-- 2. Expensive Purchase (Liability)
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '33333333-3333-3333-3333-333333333333',
  'expensive_purchase',
  'Honey, I saw you bought that {item_name}. I know you worked hard for it.

But remember what I always told you - things don''t bring lasting happiness. Financial freedom does.

That money could have been working for you, earning passive income, building your future.

I''m not judging. I just want you to think long-term. Are you building wealth or just looking wealthy?

I love you and I want the best for you.',
  'Review Budget',
  'navigate_to_profile',
  '{}',
  3,
  15,
  true
);

-- 3. Inactivity (7+ days)
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '33333333-3333-3333-3333-333333333333',
  'inactivity',
  'Sweetheart, I haven''t heard from you in a week. I''m worried.

Money problems don''t go away by ignoring them. They grow.

I know it''s hard. I know it''s overwhelming sometimes. But you''re stronger than you think.

Come back. Check your finances. Make one small decision. That''s all it takes to start.

I''m here for you. Always.',
  'Check Dashboard',
  'navigate_to_dashboard',
  '{"days_inactive_min": 7}',
  3,
  10,
  true
);

-- 4. Financial Stress (Negative Net Worth)
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '33333333-3333-3333-3333-333333333333',
  'financial_stress',
  'Honey, I see you''re struggling. Negative ${net_worth:,} net worth.

I''ve been there. It feels hopeless. But it''s not.

Every wealthy person started somewhere. Many started in debt. The difference? They didn''t give up.

Small steps. Pay off one debt. Save $10. Build one good habit. That''s how you climb out.

You''re not alone. I believe in you. Let''s do this together.',
  'Create Recovery Plan',
  'navigate_to_profile',
  '{"net_worth_max": 0}',
  4,
  20,
  true
);

-- ============================================
-- NEW COACH CHEN MESSAGES (4 additional)
-- ============================================

-- 5. Low Emergency Fund
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'low_emergency_fund',
  'Hey {username}, you have less than 3 months of expenses saved. That''s a ticking time bomb.

One job loss, one medical emergency, one car breakdown - and you''re broke.

Your emergency fund isn''t optional. It''s the foundation of financial security.

Action: Build 6 months of expenses in cash. Then invest the rest. This is non-negotiable.

The rich sleep well because they''re prepared. Be prepared.',
  'Build Emergency Fund',
  'navigate_to_profile',
  '{"emergency_fund_months_max": 3}',
  5,
  25,
  true
);

-- 6. Strong Asset Growth
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'strong_asset_growth',
  'Excellent work {username}! Your assets grew {growth_percentage}% this period.

That''s what I''m talking about - assets working FOR you, not you working for money.

But here''s the truth: Most people celebrate here and stop. Don''t be most people.

Action: Reinvest those gains. Compound growth is exponential. The next {growth_percentage}% will be easier.

This is how millionaires are made. Keep going.',
  'View Portfolio',
  'navigate_to_profile',
  '{"asset_growth_min": 0.15}',
  3,
  20,
  true
);

-- 7. No Income Diversification
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'single_income_source',
  'Listen {username}, you have ONE income source. That''s dangerous in today''s economy.

Companies downsize. Industries collapse. Jobs disappear overnight.

One income stream = one point of failure. You''re one layoff away from financial disaster.

Action: Build 2-3 additional income streams. Side hustle, investments, rental income. Diversify your income like you diversify your portfolio.

Multiple streams = financial security. Single stream = financial risk.',
  'Explore Income Options',
  'navigate_to_marketplace',
  '{"income_sources_max": 1}',
  4,
  25,
  true
);

-- 8. High Savings Rate Achievement
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'high_savings_rate',
  'Respect, {username}. You''re saving {savings_percentage}% of your income.

Most people save less than 10%. You''re in the top tier.

This is the discipline that builds wealth. Not luck. Not inheritance. Discipline.

Action: Maintain this rate. Automate it so it''s not a decision - it''s a system.

You''re doing what 95% of people won''t do. That''s why you''ll have what 95% won''t have.',
  'View Savings',
  'navigate_to_profile',
  '{"savings_rate_min": 0.3}',
  3,
  20,
  true
);

-- ============================================
-- NEW TASHA MESSAGES (4 additional)
-- ============================================

-- 5. Poor Credit Score
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '22222222-2222-2222-2222-222222222222',
  'poor_credit_score',
  'Hi {username}, your credit score is {credit_score}. That''s costing you thousands.

Low credit = higher interest rates on everything. Loans, mortgages, even insurance.

A bad credit score is like a tax on being poor. The system punishes you for struggling.

Action: Pay bills on time. Keep credit utilization under 30%. Dispute errors. It takes 6-12 months to rebuild.

Your credit score is your financial reputation. Protect it.',
  'Improve Credit',
  'navigate_to_profile',
  '{"credit_score_max": 650}',
  4,
  25,
  true
);

-- 6. No Asset Ownership
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '22222222-2222-2222-2222-222222222222',
  'no_assets',
  'Hi {username}, I need to be direct with you.

You own zero income-generating assets. That means you''re 100% dependent on your job.

If you stop working, your income stops. That''s not a financial plan - that''s a treadmill.

Action: Buy your first asset this month. Even $100 in dividend stocks. Start somewhere.

Assets = freedom. No assets = permanent employment. Choose wisely.',
  'Buy First Asset',
  'navigate_to_marketplace',
  '{"total_assets_max": 0}',
  5,
  30,
  true
);

-- 7. Excellent Debt Management
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '22222222-2222-2222-2222-222222222222',
  'low_debt_ratio',
  'Hi {username}, impressive. Your debt-to-income ratio is only {debt_percentage}%.

You''re managing debt responsibly. That''s rare discipline.

Most people let debt control them. You''re controlling your debt.

Action: Keep this ratio under 20%. Use the extra cash flow to invest, not to take on more debt.

This is how you build wealth - by NOT owing it to someone else.',
  'View Debt Status',
  'navigate_to_loans',
  '{"debt_to_income_max": 0.2}',
  3,
  15,
  true
);

-- 8. Stagnant Income
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '22222222-2222-2222-2222-222222222222',
  'stagnant_income',
  'Hi {username}, your income hasn''t grown in {months_stagnant} months.

Inflation is eating your purchasing power. You''re effectively getting a pay cut.

If your income isn''t growing, you''re falling behind. That''s the harsh reality.

Action: Ask for a raise. Switch jobs. Start a side income. Do something.

Staying comfortable is how you stay broke. Growth requires discomfort.',
  'Increase Income',
  'navigate_to_jobs',
  '{"income_growth_months_max": 6}',
  4,
  20,
  true
);

-- ============================================
-- NEW PARENT MESSAGES (4 additional)
-- ============================================

-- 5. First Asset Purchase
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '33333333-3333-3333-3333-333333333333',
  'first_asset',
  'Sweetheart, you bought your first asset! I''m so proud.

This is a big moment. You''re not just earning money - you''re making money work for you.

I wish I had started this young. You''re ahead of where I was at your age.

Keep going. This is just the beginning of building real wealth.

Love you so much,
Mom/Dad',
  'View Assets',
  'navigate_to_profile',
  '{"asset_count_min": 1, "asset_count_max": 1}',
  3,
  15,
  true
);

-- 6. Consistent Progress
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '33333333-3333-3333-3333-333333333333',
  'consistent_progress',
  'Honey, I''ve been watching you. {months_active} months of consistent financial progress.

That''s not luck. That''s discipline. That''s character.

Most people give up after a few weeks. You''re still here, still growing.

I''m so proud of the person you''re becoming. Not just financially - in every way.

Keep going. I believe in you.

Love always,
Mom/Dad',
  'View Progress',
  'navigate_to_profile',
  '{"months_active_min": 6}',
  3,
  20,
  true
);

-- 7. Debt Freedom Achievement
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '33333333-3333-3333-3333-333333333333',
  'debt_free',
  'Sweetheart, you did it. Zero debt. I''m crying happy tears.

I know how hard you worked for this. The sacrifices you made. The discipline it took.

Being debt-free is freedom. Real freedom. You don''t owe anyone anything.

Now you can build wealth without the weight of debt holding you back.

I''m so incredibly proud of you.

Love you forever,
Mom/Dad',
  'Celebrate Achievement',
  'share_milestone',
  '{"total_debt_max": 0, "had_debt_before": true}',
  2,
  50,
  true
);

-- 8. Work-Life Balance Concern
INSERT INTO mentor_messages (mentor_id, trigger_type, message_template, cta_text, cta_action, trigger_conditions, priority, points_reward, is_active) VALUES
(
  '33333333-3333-3333-3333-333333333333',
  'overworking',
  'Honey, I''m worried. You''re working {hours_per_week} hours a week.

Money is important, but so is your health. Your relationships. Your happiness.

I don''t want you to wake up at 50, wealthy but alone and burned out.

Remember: You''re building wealth to enjoy life, not sacrificing life to build wealth.

Take a break. Rest. Spend time with people you love.

I love you more than any amount of money,
Mom/Dad',
  'Review Schedule',
  'navigate_to_profile',
  '{"work_hours_min": 60}',
  3,
  15,
  true
);
