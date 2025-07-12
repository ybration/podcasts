#!/usr/bin/env python3
"""
RSS Feed Manager - Expand and clean podcast feeds from Podcastindex

This script:
1. Loads existing feeds.json
2. Processes Podcastindex database
3. Validates RSS feeds
4. Removes duplicates
5. Scores feed quality
6. Updates feeds.json with best feeds
"""

import csv
import json
import requests
import feedparser
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urlparse
import hashlib

class FeedManager:
    """Manage RSS feed collection and quality"""
    
    def __init__(self):
        self.existing_feeds = []
        self.podcastindex_feeds = []
        self.validated_feeds = []
        self.duplicate_urls = set()
        
    def load_existing_feeds(self, feeds_file: str = 'feeds.json') -> List[Dict]:
        """Load current feeds.json"""
        try:
            with open(feeds_file, 'r') as f:
                self.existing_feeds = json.load(f)
            print(f"✅ Loaded {len(self.existing_feeds)} existing feeds")
            return self.existing_feeds
        except FileNotFoundError:
            print("❌ feeds.json not found")
            return []
    
    def load_podcastindex_data(self, csv_file: str = 'podcastindex-db/db_newsfeeds_1000rows.csv') -> List[Dict]:
        """Load Podcastindex CSV data"""
        feeds = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    feeds.append(row)
            print(f"✅ Loaded {len(feeds)} feeds from Podcastindex")
            self.podcastindex_feeds = feeds
            return feeds
        except Exception as e:
            print(f"❌ Error loading Podcastindex data: {e}")
            return []
    
    def clean_podcastindex_feeds(self) -> List[Dict]:
        """Filter out dead, bad, and irrelevant feeds"""
        cleaned = []
        
        for feed in self.podcastindex_feeds:
            # Skip dead feeds
            if feed.get('dead', '0') == '1':
                continue
                
            # Skip feeds with too many parse errors (more lenient)
            if int(feed.get('parse_errors', 0)) > 10:
                continue
                
            # Skip if URL is malformed
            url = feed.get('url', '').strip()
            if not url or not url.startswith(('http://', 'https://')):
                continue
                
            # Skip duplicate URLs from Podcastindex itself (NULL means no duplicate)
            if feed.get('duplicateof') and feed.get('duplicateof') != 'NULL':
                continue
            
            # Basic title check
            title = feed.get('title', '').strip()
            if not title or len(title) < 3:
                continue
            
            cleaned.append(feed)
        
        print(f"✅ Cleaned: {len(cleaned)} feeds from {len(self.podcastindex_feeds)}")
        return cleaned
    
    def validate_rss_feed(self, url: str, timeout: int = 10) -> Tuple[bool, Dict]:
        """Validate RSS feed and return quality metrics"""
        try:
            # Parse feed
            feed = feedparser.parse(url)
            
            # Check if feed parsed successfully
            if feed.bozo and not feed.entries:
                return False, {'error': 'Failed to parse feed'}
            
            # Check for minimum content
            if len(feed.entries) < 3:
                return False, {'error': 'Too few episodes'}
            
            # Check for recent content (last 6 months)
            recent_episodes = 0
            cutoff = datetime.now() - timedelta(days=180)
            
            for entry in feed.entries[:10]:  # Check first 10 episodes
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date > cutoff:
                        recent_episodes += 1
            
            if recent_episodes == 0:
                return False, {'error': 'No recent episodes'}
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(feed)
            
            return True, {
                'title': feed.feed.get('title', 'Unknown'),
                'description': feed.feed.get('description', ''),
                'total_episodes': len(feed.entries),
                'recent_episodes': recent_episodes,
                'quality_score': quality_score,
                'language': feed.feed.get('language', 'en'),
                'author': feed.feed.get('author', ''),
                'image_url': self.extract_image_url(feed),
                'categories': self.extract_categories(feed)
            }
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def calculate_quality_score(self, feed) -> float:
        """Calculate feed quality score (0-100)"""
        score = 0
        
        # Episode count (max 20 points)
        episode_count = len(feed.entries)
        score += min(episode_count / 10, 20)
        
        # Recent activity (max 25 points)
        recent_count = 0
        cutoff = datetime.now() - timedelta(days=30)
        for entry in feed.entries[:20]:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date > cutoff:
                        recent_count += 1
                except:
                    pass
        score += min(recent_count * 5, 25)
        
        # Metadata quality (max 25 points)
        if feed.feed.get('title'):
            score += 5
        if feed.feed.get('description'):
            score += 5
        if feed.feed.get('author'):
            score += 5
        if feed.feed.get('language'):
            score += 5
        if hasattr(feed.feed, 'image') or feed.feed.get('logo'):
            score += 5
        
        # Episode metadata quality (max 30 points)
        metadata_score = 0
        for entry in feed.entries[:5]:
            if entry.get('title'):
                metadata_score += 2
            if entry.get('description'):
                metadata_score += 2
            if hasattr(entry, 'enclosures') and entry.enclosures:
                metadata_score += 2
        score += min(metadata_score, 30)
        
        return round(score, 1)
    
    def extract_image_url(self, feed) -> str:
        """Extract best available image URL"""
        if hasattr(feed.feed, 'image') and 'href' in feed.feed.image:
            return feed.feed.image.href
        elif feed.feed.get('logo'):
            return feed.feed.logo
        return ''
    
    def extract_categories(self, feed) -> List[str]:
        """Extract categories from feed"""
        categories = []
        
        # iTunes categories
        if hasattr(feed.feed, 'tags'):
            for tag in feed.feed.tags:
                if tag.get('term'):
                    categories.append(tag.term)
        
        # Fallback to description-based categorization
        if not categories:
            description = feed.feed.get('description', '').lower()
            if any(word in description for word in ['tech', 'technology', 'programming']):
                categories.append('Technology')
            elif any(word in description for word in ['news', 'politics', 'current']):
                categories.append('News')
            elif any(word in description for word in ['business', 'entrepreneur', 'finance']):
                categories.append('Business')
            elif any(word in description for word in ['science', 'research', 'education']):
                categories.append('Science')
            elif any(word in description for word in ['comedy', 'humor', 'funny']):
                categories.append('Comedy')
            else:
                categories.append('General')
        
        return categories[:3]  # Limit to 3 categories
    
    def detect_duplicates(self, feeds: List[Dict]) -> Set[str]:
        """Detect duplicate feeds by URL and title similarity"""
        seen_urls = set()
        seen_titles = {}
        duplicates = set()
        
        for feed in feeds:
            url = feed.get('url', '').lower().strip('/')
            title = feed.get('title', '').lower().strip()
            
            # URL duplicates
            if url in seen_urls:
                duplicates.add(url)
            else:
                seen_urls.add(url)
            
            # Title similarity (fuzzy matching)
            if title:
                # Simple title deduplication
                title_key = re.sub(r'[^a-z0-9]', '', title)
                if title_key in seen_titles:
                    # Keep the one with higher quality score
                    existing_feed = seen_titles[title_key]
                    current_score = feed.get('quality_score', 0)
                    existing_score = existing_feed.get('quality_score', 0)
                    
                    if current_score > existing_score:
                        duplicates.add(existing_feed.get('url'))
                        seen_titles[title_key] = feed
                    else:
                        duplicates.add(url)
                else:
                    seen_titles[title_key] = feed
        
        return duplicates
    
    def process_feeds_batch(self, feeds: List[Dict], batch_size: int = 10) -> List[Dict]:
        """Process feeds in batches to avoid overwhelming servers"""
        validated = []
        total = len(feeds)
        
        for i in range(0, total, batch_size):
            batch = feeds[i:i + batch_size]
            print(f"🔄 Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
            
            for feed in batch:
                url = feed.get('url')
                if not url:
                    continue
                    
                print(f"  ⏳ Validating: {feed.get('title', url)}")
                is_valid, metrics = self.validate_rss_feed(url)
                
                if is_valid:
                    feed_data = {
                        'rss_url': url,
                        'title': metrics['title'],
                        'description': metrics['description'][:200],  # Limit description
                        'categories': metrics['categories'],
                        'language': metrics['language'],
                        'quality_score': metrics['quality_score'],
                        'total_episodes': metrics['total_episodes'],
                        'recent_episodes': metrics['recent_episodes']
                    }
                    validated.append(feed_data)
                    print(f"    ✅ Valid (score: {metrics['quality_score']})")
                else:
                    print(f"    ❌ Invalid: {metrics.get('error', 'Unknown error')}")
                
                # Be respectful to servers
                time.sleep(1)
            
            # Longer pause between batches
            if i + batch_size < total:
                print("  💤 Pausing between batches...")
                time.sleep(5)
        
        return validated
    
    def merge_feeds(self, existing: List[Dict], new_feeds: List[Dict], max_feeds: int = 100) -> List[Dict]:
        """Merge existing and new feeds, prioritizing quality"""
        
        # Convert existing feeds to same format
        existing_normalized = []
        for feed in existing:
            existing_normalized.append({
                'rss_url': feed.get('rss_url'),
                'title': feed.get('title'),
                'categories': feed.get('categories', []),
                'language': feed.get('language', 'en'),
                'quality_score': 100,  # Assume existing feeds are high quality
                'existing': True
            })
        
        # Combine all feeds
        all_feeds = existing_normalized + new_feeds
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_feeds = []
        for feed in all_feeds:
            url = feed.get('rss_url', '').lower()
            if url not in seen_urls:
                seen_urls.add(url)
                unique_feeds.append(feed)
        
        # Sort by quality score (existing feeds first, then by score)
        unique_feeds.sort(key=lambda x: (
            0 if x.get('existing') else 1,  # Existing feeds first
            -x.get('quality_score', 0)      # Then by quality score desc
        ))
        
        # Take top feeds
        final_feeds = unique_feeds[:max_feeds]
        
        # Convert back to feeds.json format
        output_feeds = []
        for feed in final_feeds:
            output_feeds.append({
                'rss_url': feed['rss_url'],
                'title': feed['title'],
                'categories': feed['categories'],
                'language': feed['language']
            })
        
        return output_feeds
    
    def save_feeds(self, feeds: List[Dict], output_file: str = 'feeds_expanded.json'):
        """Save processed feeds to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(feeds, f, indent=2)
        print(f"✅ Saved {len(feeds)} feeds to {output_file}")

def main():
    """Main processing function"""
    manager = FeedManager()
    
    print("🎙️ RSS Feed Manager - Expanding Podcast Collection")
    print("=" * 50)
    
    # Load existing feeds
    existing = manager.load_existing_feeds()
    
    # Load Podcastindex data
    podcastindex_raw = manager.load_podcastindex_data()
    
    if not podcastindex_raw:
        print("❌ Cannot proceed without Podcastindex data")
        return
    
    # Clean Podcastindex feeds
    cleaned_feeds = manager.clean_podcastindex_feeds()
    
    # Process top feeds (limit for testing)
    print(f"\n🔄 Processing top 50 feeds for validation...")
    top_feeds = cleaned_feeds[:50]  # Start with top 50 for testing
    
    validated = manager.process_feeds_batch(top_feeds, batch_size=5)
    
    print(f"\n📊 Validation Results:")
    print(f"  - Processed: {len(top_feeds)} feeds")
    print(f"  - Valid: {len(validated)} feeds")
    if len(top_feeds) > 0:
        print(f"  - Success rate: {len(validated)/len(top_feeds)*100:.1f}%")
    else:
        print(f"  - No feeds to process")
    
    # Merge with existing feeds
    final_feeds = manager.merge_feeds(existing, validated, max_feeds=50)
    
    print(f"\n📝 Final Results:")
    print(f"  - Existing feeds: {len(existing)}")
    print(f"  - New feeds added: {len(final_feeds) - len(existing)}")
    print(f"  - Total feeds: {len(final_feeds)}")
    
    # Save results
    manager.save_feeds(final_feeds, 'feeds_expanded.json')
    
    print(f"\n🎉 Feed expansion complete!")
    print(f"Review 'feeds_expanded.json' and replace 'feeds.json' when ready.")

if __name__ == "__main__":
    main()