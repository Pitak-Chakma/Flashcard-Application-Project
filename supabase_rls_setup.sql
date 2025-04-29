-- Supabase RLS (Row Level Security) Setup
-- This script sets up the necessary RLS policies for the Flashcard Application

-- First, enable RLS on all tables (it's likely already enabled by default)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_reviews ENABLE ROW LEVEL SECURITY;

-- Create a policy for the users table to allow inserts from authenticated and anon users
-- This is necessary for registration to work
CREATE POLICY "Allow public registration" ON users
    FOR INSERT 
    WITH CHECK (true);

-- Create a policy to allow users to read their own data
CREATE POLICY "Users can read own data" ON users
    FOR SELECT
    USING (auth.uid() = id OR auth.role() = 'anon');

-- Create a policy to allow users to update their own data
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Create a policy for the cards table to allow users to manage their own cards
CREATE POLICY "Users can manage own cards" ON cards
    FOR ALL
    USING (auth.uid() = user_id OR user_id IS NULL);

-- Create a policy for public cards to be visible to everyone
CREATE POLICY "Public cards are visible to everyone" ON cards
    FOR SELECT
    USING (is_public = true);

-- Create a policy for the tags table to allow all operations
-- Tags are generally shared resources
CREATE POLICY "Tags are accessible to all" ON tags
    FOR ALL
    USING (true);

-- Create a policy for the card_tags junction table
CREATE POLICY "Users can manage tags for their own cards" ON card_tags
    FOR ALL
    USING (EXISTS (
        SELECT 1 FROM cards 
        WHERE cards.id = card_tags.card_id 
        AND (cards.user_id = auth.uid() OR cards.is_public = true)
    ));

-- Create a policy for the card_reviews table
CREATE POLICY "Users can manage their own reviews" ON card_reviews
    FOR ALL
    USING (user_id = auth.uid() OR user_id IS NULL);

-- IMPORTANT: For development purposes, you can temporarily bypass RLS
-- This will allow all operations regardless of user, which is useful during development
-- WARNING: Do not use this in production!

-- Option 1: Disable RLS on all tables (temporary development solution)
-- ALTER TABLE users DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE cards DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE tags DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE card_tags DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE card_reviews DISABLE ROW LEVEL SECURITY;

-- Option 2: Create a policy that allows all operations (temporary development solution)
CREATE POLICY "Allow all operations for development" ON users FOR ALL USING (true);
CREATE POLICY "Allow all operations for development" ON cards FOR ALL USING (true);
CREATE POLICY "Allow all operations for development" ON tags FOR ALL USING (true);
CREATE POLICY "Allow all operations for development" ON card_tags FOR ALL USING (true);
CREATE POLICY "Allow all operations for development" ON card_reviews FOR ALL USING (true);
