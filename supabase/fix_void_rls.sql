-- Enable Row Level Security
ALTER TABLE void_posts ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Allow authenticated users to view all posts" ON void_posts;
DROP POLICY IF EXISTS "Allow authenticated users to insert their own posts" ON void_posts;
DROP POLICY IF EXISTS "Allow users to update own posts" ON void_posts;
DROP POLICY IF EXISTS "Allow users to delete own posts" ON void_posts;

-- 1. Allow authenticated users to view ALL posts (so they can see the feed)
CREATE POLICY "Allow authenticated users to view all posts"
ON void_posts FOR SELECT
TO authenticated
USING (true);

-- 2. Allow authenticated users to insert their OWN posts
-- The CHECK clause ensures the user_id in the row matches the authenticated user's ID
CREATE POLICY "Allow authenticated users to insert their own posts"
ON void_posts FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- 3. Allow users to update only their own posts
CREATE POLICY "Allow users to update own posts"
ON void_posts FOR UPDATE
TO authenticated
USING (auth.uid() = user_id);

-- 4. Allow users to delete only their own posts
CREATE POLICY "Allow users to delete own posts"
ON void_posts FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Verify policies for void_reactions table (Reaction logic needs this too)
ALTER TABLE void_reactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow authenticated users to view all reactions" ON void_reactions;
DROP POLICY IF EXISTS "Allow authenticated users to manage own reactions" ON void_reactions;

CREATE POLICY "Allow authenticated users to view all reactions"
ON void_reactions FOR SELECT
TO authenticated
USING (true);

-- Allow insert/update/delete for own reactions
CREATE POLICY "Allow authenticated users to manage own reactions"
ON void_reactions FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);
