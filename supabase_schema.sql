-- Podcast Metadata System - Supabase Schema
-- Run this in your Supabase SQL editor to create the database structure

-- Create podcasts table
CREATE TABLE IF NOT EXISTS podcasts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    rss_url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    author TEXT,
    language TEXT DEFAULT 'en',
    image_url TEXT,
    categories TEXT[], -- Array of category strings
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
    duration INTEGER, -- Duration in seconds
    audio_url TEXT,
    episode_type TEXT DEFAULT 'full', -- full, trailer, bonus
    season_number INTEGER,
    episode_number INTEGER,
    is_explicit BOOLEAN DEFAULT false,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_podcasts_rss_url ON podcasts(rss_url);
CREATE INDEX IF NOT EXISTS idx_podcasts_categories ON podcasts USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_podcasts_language ON podcasts(language);
CREATE INDEX IF NOT EXISTS idx_podcasts_latest_episode_date ON podcasts(latest_episode_date DESC);

CREATE INDEX IF NOT EXISTS idx_episodes_podcast_id ON episodes(podcast_id);
CREATE INDEX IF NOT EXISTS idx_episodes_published_at ON episodes(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_episodes_episode_type ON episodes(episode_type);

-- Enable full-text search on titles and descriptions
CREATE INDEX IF NOT EXISTS idx_podcasts_search ON podcasts USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_episodes_search ON episodes USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Note: Removed triggers to avoid function dependency issues
-- Tables will still work perfectly for the podcast system