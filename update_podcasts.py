#!/usr/bin/env python3
"""
Podcast RSS Feed Parser and Supabase Uploader

This script:
1. Loads podcast RSS URLs from feeds.json
2. Parses each RSS feed using feedparser
3. Extracts podcast and episode metadata
4. Uploads data to Supabase via REST API
"""

import json
import os
import sys
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import feedparser
import requests
from dateutil import parser as date_parser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupabaseClient:
    """Simple Supabase REST API client"""
    
    def __init__(self, url: str, api_key: str):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'apikey': api_key,
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
    
    def upsert(self, table: str, data: Dict[str, Any], conflict_column: str = None) -> bool:
        """Insert or update data in Supabase table"""
        url = f"{self.url}/rest/v1/{table}"
        
        # Use upsert with conflict resolution
        headers = self.headers.copy()
        if conflict_column:
            headers['Prefer'] = f'resolution=merge-duplicates'
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upsert to {table}: {e}")
            return False
    
    def select(self, table: str, columns: str = "*", filters: str = "") -> Optional[List[Dict]]:
        """Select data from Supabase table"""
        url = f"{self.url}/rest/v1/{table}"
        if columns != "*":
            url += f"?select={columns}"
        if filters:
            separator = "&" if "?" in url else "?"
            url += f"{separator}{filters}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to select from {table}: {e}")
            return None

class PodcastProcessor:
    """Process podcast RSS feeds and upload to Supabase"""
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.max_episodes_per_podcast = 50  # Limit to recent episodes
    
    def parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string to seconds"""
        if not duration_str:
            return None
        
        try:
            # Handle formats like "HH:MM:SS", "MM:SS", or just seconds
            parts = duration_str.strip().split(':')
            if len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            else:  # Just seconds
                return int(float(duration_str))
        except (ValueError, IndexError):
            return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats to datetime"""
        if not date_str:
            return None
        
        try:
            return date_parser.parse(date_str).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None
    
    def extract_podcast_metadata(self, feed: feedparser.FeedParserDict, manual_data: Dict) -> Dict[str, Any]:
        """Extract podcast-level metadata from RSS feed"""
        podcast_data = {
            'rss_url': manual_data['rss_url'],
            'title': feed.feed.get('title', manual_data.get('title', 'Unknown Podcast')),
            'description': feed.feed.get('description', ''),
            'author': feed.feed.get('author', feed.feed.get('publisher', '')),
            'language': feed.feed.get('language', manual_data.get('language', 'en')),
            'image_url': '',
            'categories': manual_data.get('categories', []),
            'is_explicit': False,
            'country': manual_data.get('country', ''),
            'total_episodes': len(feed.entries),
            'latest_episode_date': None,
        }
        
        # Extract image URL
        if hasattr(feed.feed, 'image') and 'href' in feed.feed.image:
            podcast_data['image_url'] = feed.feed.image.href
        elif hasattr(feed.feed, 'logo'):
            podcast_data['image_url'] = feed.feed.logo
        
        # Check for explicit content
        if hasattr(feed.feed, 'itunes_explicit'):
            podcast_data['is_explicit'] = feed.feed.itunes_explicit.lower() in ['yes', 'true']
        
        # Get latest episode date
        if feed.entries:
            latest_entry = feed.entries[0]
            if hasattr(latest_entry, 'published'):
                podcast_data['latest_episode_date'] = self.parse_date(latest_entry.published)
        
        return podcast_data
    
    def extract_episode_metadata(self, entry: feedparser.FeedParserDict, podcast_id: str) -> Dict[str, Any]:
        """Extract episode-level metadata from RSS entry"""
        episode_data = {
            'podcast_id': podcast_id,
            'title': entry.get('title', 'Untitled Episode'),
            'description': entry.get('description', entry.get('summary', '')),
            'published_at': self.parse_date(entry.get('published', '')),
            'duration': None,
            'audio_url': '',
            'episode_type': 'full',
            'season_number': None,
            'episode_number': None,
            'is_explicit': False,
            'image_url': '',
        }
        
        # Extract audio URL from enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.type and 'audio' in enclosure.type:
                    episode_data['audio_url'] = enclosure.href
                    break
        
        # Extract duration
        if hasattr(entry, 'itunes_duration'):
            episode_data['duration'] = self.parse_duration(entry.itunes_duration)
        
        # Extract episode type
        if hasattr(entry, 'itunes_episodetype'):
            episode_data['episode_type'] = entry.itunes_episodetype
        
        # Extract season/episode numbers
        if hasattr(entry, 'itunes_season'):
            try:
                episode_data['season_number'] = int(entry.itunes_season)
            except (ValueError, TypeError):
                pass
        
        if hasattr(entry, 'itunes_episode'):
            try:
                episode_data['episode_number'] = int(entry.itunes_episode)
            except (ValueError, TypeError):
                pass
        
        # Check for explicit content
        if hasattr(entry, 'itunes_explicit'):
            episode_data['is_explicit'] = entry.itunes_explicit.lower() in ['yes', 'true']
        
        # Extract episode image
        if hasattr(entry, 'image') and 'href' in entry.image:
            episode_data['image_url'] = entry.image.href
        
        return episode_data
    
    def process_podcast(self, manual_data: Dict) -> bool:
        """Process a single podcast RSS feed"""
        rss_url = manual_data['rss_url']
        logger.info(f"Processing podcast: {manual_data.get('title', rss_url)}")
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if feed.bozo and not feed.entries:
                logger.error(f"Failed to parse RSS feed: {rss_url}")
                return False
            
            # Extract podcast metadata
            podcast_data = self.extract_podcast_metadata(feed, manual_data)
            
            # Upload podcast data
            if not self.supabase.upsert('podcasts', podcast_data, 'rss_url'):
                logger.error(f"Failed to upload podcast data for: {rss_url}")
                return False
            
            # Get podcast ID from database
            podcast_records = self.supabase.select('podcasts', 'id', f'rss_url=eq.{rss_url}')
            if not podcast_records:
                logger.error(f"Failed to retrieve podcast ID for: {rss_url}")
                return False
            
            podcast_id = podcast_records[0]['id']
            
            # Process episodes (limit to recent ones)
            episodes_processed = 0
            for entry in feed.entries[:self.max_episodes_per_podcast]:
                episode_data = self.extract_episode_metadata(entry, podcast_id)
                
                if self.supabase.upsert('episodes', episode_data):
                    episodes_processed += 1
                else:
                    logger.warning(f"Failed to upload episode: {episode_data['title']}")
            
            logger.info(f"Successfully processed {episodes_processed} episodes for podcast: {podcast_data['title']}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing podcast {rss_url}: {e}")
            return False
    
    def process_all_podcasts(self, feeds_file: str) -> None:
        """Process all podcasts from feeds.json file"""
        try:
            with open(feeds_file, 'r') as f:
                feeds_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load feeds file {feeds_file}: {e}")
            return
        
        total_podcasts = len(feeds_data)
        successful_podcasts = 0
        
        logger.info(f"Starting to process {total_podcasts} podcasts")
        
        for i, podcast_data in enumerate(feeds_data, 1):
            logger.info(f"Processing podcast {i}/{total_podcasts}")
            
            if self.process_podcast(podcast_data):
                successful_podcasts += 1
            
            # Add small delay to be respectful to RSS servers
            time.sleep(1)
        
        logger.info(f"Completed processing. Successfully updated {successful_podcasts}/{total_podcasts} podcasts")

def main():
    """Main function"""
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    # Initialize Supabase client
    supabase_client = SupabaseClient(supabase_url, supabase_key)
    
    # Initialize podcast processor
    processor = PodcastProcessor(supabase_client)
    
    # Process all podcasts
    feeds_file = os.path.join(os.path.dirname(__file__), 'feeds.json')
    processor.process_all_podcasts(feeds_file)

if __name__ == "__main__":
    main()