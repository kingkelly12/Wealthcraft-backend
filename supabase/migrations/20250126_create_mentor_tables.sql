-- Create mentors table
CREATE TABLE IF NOT EXISTS mentors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    personality TEXT NOT NULL,
    avatar_url TEXT,
    greeting_template TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create mentor_messages table
CREATE TABLE IF NOT EXISTS mentor_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentor_id UUID NOT NULL REFERENCES mentors(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL,
    message_template TEXT NOT NULL,
    cta_text VARCHAR(100),
    cta_action VARCHAR(50),
    trigger_conditions JSONB DEFAULT '{}',
    min_net_worth DECIMAL(15, 2),
    max_net_worth DECIMAL(15, 2),
    priority INTEGER DEFAULT 1,
    points_reward INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create player_mentor_interactions table
CREATE TABLE IF NOT EXISTS player_mentor_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL,
    mentor_id UUID NOT NULL REFERENCES mentors(id) ON DELETE CASCADE,
    message_id UUID REFERENCES mentor_messages(id) ON DELETE SET NULL,
    message_content TEXT NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    player_data_snapshot JSONB DEFAULT '{}',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    action_taken BOOLEAN DEFAULT FALSE,
    action_taken_at TIMESTAMP WITH TIME ZONE,
    points_earned INTEGER DEFAULT 0,
    relationship_score INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_mentor_messages_mentor_id ON mentor_messages(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_messages_trigger_type ON mentor_messages(trigger_type);
CREATE INDEX IF NOT EXISTS idx_player_mentor_interactions_player_id ON player_mentor_interactions(player_id);
CREATE INDEX IF NOT EXISTS idx_player_mentor_interactions_mentor_id ON player_mentor_interactions(mentor_id);
CREATE INDEX IF NOT EXISTS idx_player_mentor_interactions_sent_at ON player_mentor_interactions(sent_at DESC);

-- Enable Row Level Security
ALTER TABLE mentors ENABLE ROW LEVEL SECURITY;
ALTER TABLE mentor_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_mentor_interactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for mentors (public read)
CREATE POLICY "Mentors are viewable by everyone"
    ON mentors FOR SELECT
    USING (true);

-- RLS Policies for mentor_messages (public read)
CREATE POLICY "Mentor messages are viewable by everyone"
    ON mentor_messages FOR SELECT
    USING (true);

-- RLS Policies for player_mentor_interactions (users can only see their own)
CREATE POLICY "Users can view their own mentor interactions"
    ON player_mentor_interactions FOR SELECT
    USING (auth.uid() = player_id);

CREATE POLICY "Users can update their own mentor interactions"
    ON player_mentor_interactions FOR UPDATE
    USING (auth.uid() = player_id);

CREATE POLICY "System can insert mentor interactions"
    ON player_mentor_interactions FOR INSERT
    WITH CHECK (true);
