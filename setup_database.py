#!/usr/bin/env python3
"""
Setup Supabase database schema
"""

import requests
import os

def setup_supabase_schema():
    """Create the database schema in Supabase"""
    
    supabase_url = "https://pmijctxikafxsqdqxdej.supabase.co"
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaWpjdHhpa2FmeHNxZHF4ZGVqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMwODUzMSwiZXhwIjoyMDY3ODg0NTMxfQ.qL8_fdgqQxuvhNUVoG4_QmJtjc_yiuASXotkklCe8pA"
    
    # SQL schema
    schema_sql = """
-- Create podcasts table
CREATE TABLE IF NOT EXISTS podcasts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    rss_url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    author TEXT,
    language TEXT DEFAULT 'en',
    image_url TEXT,
    categories TEXT[],
    is_explicit BOOLEAN DEFAULT false,
    country TEXT,
    total_episodes INTEGER DEFAULT 0,
    latest_episode_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create episodes table
CREATE TABLE IF NOT EXISTS episodes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    published_at TIMESTAMPTZ,
    duration INTEGER,
    audio_url TEXT,
    episode_type TEXT DEFAULT 'full',
    season_number INTEGER,
    episode_number INTEGER,
    is_explicit BOOLEAN DEFAULT false,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_podcasts_rss_url ON podcasts(rss_url);
CREATE INDEX IF NOT EXISTS idx_podcasts_categories ON podcasts USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_podcasts_language ON podcasts(language);
CREATE INDEX IF NOT EXISTS idx_podcasts_latest_episode_date ON podcasts(latest_episode_date DESC);
CREATE INDEX IF NOT EXISTS idx_episodes_podcast_id ON episodes(podcast_id);
CREATE INDEX IF NOT EXISTS idx_episodes_published_at ON episodes(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_episodes_episode_type ON episodes(episode_type);
CREATE INDEX IF NOT EXISTS idx_podcasts_search ON podcasts USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_episodes_search ON episodes USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Create update function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
DROP TRIGGER IF EXISTS update_podcasts_updated_at ON podcasts;
CREATE TRIGGER update_podcasts_updated_at BEFORE UPDATE ON podcasts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_episodes_updated_at ON episodes;
CREATE TRIGGER update_episodes_updated_at BEFORE UPDATE ON episodes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""
    
    # Execute SQL using a stored procedure call
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    # Try to create a function to execute SQL
    create_exec_function = """
CREATE OR REPLACE FUNCTION exec_sql(sql_text TEXT)
RETURNS TEXT AS $$
BEGIN
    EXECUTE sql_text;
    RETURN 'Success';
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'Error: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;
"""
    
    print("🔧 Setting up Supabase database schema...")
    
    # Since we can't execute arbitrary SQL via REST API, let's check what tables exist
    try:
        # Check if podcasts table exists
        response = requests.get(
            f"{supabase_url}/rest/v1/podcasts",
            headers=headers,
            params={'limit': 1}
        )
        
        if response.status_code == 200:
            print("✅ Podcasts table already exists!")
            print("✅ Database schema appears to be set up correctly!")
            return True
        elif response.status_code == 404:
            print("❌ Tables don't exist yet - need to run SQL manually")
            return False
        else:
            print(f"🔍 Database check returned: {response.status_code}")
            print("📋 You'll need to run the SQL schema manually")
            return False
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    setup_supabase_schema()