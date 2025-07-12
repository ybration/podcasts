#!/usr/bin/env python3
"""
Scale to 100+ Premium Podcast Feeds
Target: Add 70+ more high-quality feeds across diverse categories
"""

import csv
import json
import feedparser
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

class PremiumScaler:
    """Scale to 100+ premium podcast feeds"""
    
    def __init__(self, min_score: int = 55):  # Slightly lower threshold for diversity
        self.min_score = min_score
        self.existing_feeds = []
        self.target_categories = {
            'Technology': 15,
            'Business': 12, 
            'News': 10,
            'Science': 8,
            'Comedy': 8,
            'Health': 6,
            'Sports': 6,
            'Education': 5,
            'True Crime': 5,
            'Music': 5,
            'Arts': 4,
            'Politics': 4,
            'Society': 4,
            'History': 3,
            'Finance': 3,
            'Food': 2
        }
        
    def load_existing_feeds(self) -> List[Dict]:
        """Load current feeds.json"""
        try:
            with open('feeds.json', 'r') as f:
                self.existing_feeds = json.load(f)
            print(f"✅ Current feeds: {len(self.existing_feeds)}")
            
            # Analyze current categories
            category_count = defaultdict(int)
            for feed in self.existing_feeds:
                for cat in feed.get('categories', []):
                    category_count[cat] += 1
            
            print("📊 Current category distribution:")
            for cat, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True):
                print(f"   {cat}: {count}")
                
            return self.existing_feeds
        except FileNotFoundError:
            print("❌ feeds.json not found")
            return []
    
    def get_strategic_candidates(self, limit: int = 500) -> List[Dict]:
        """Get strategically selected candidates for category balance"""
        candidates = []
        
        # Priority keywords for each category
        category_keywords = {
            'Technology': ['tech', 'programming', 'software', 'ai', 'startup', 'coding', 'developer'],
            'Business': ['business', 'entrepreneur', 'startup', 'marketing', 'finance', 'leadership'],
            'News': ['news', 'politics', 'current', 'journalism', 'daily', 'weekly'],
            'Science': ['science', 'research', 'physics', 'biology', 'chemistry', 'space'],
            'Comedy': ['comedy', 'humor', 'funny', 'laugh', 'standup', 'improv'],
            'Health': ['health', 'fitness', 'wellness', 'medical', 'nutrition', 'mental'],
            'Sports': ['sports', 'football', 'basketball', 'baseball', 'soccer', 'fitness'],
            'Education': ['education', 'learning', 'teaching', 'university', 'academic'],
            'True Crime': ['crime', 'murder', 'investigation', 'detective', 'mystery'],
            'Music': ['music', 'artist', 'album', 'song', 'musician', 'band'],
            'History': ['history', 'historical', 'ancient', 'war', 'civilization'],
            'Finance': ['finance', 'money', 'investing', 'stocks', 'crypto', 'economy']
        }
        
        try:
            with open('podcastindex-db/db_newsfeeds_1000rows.csv', 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Pre-filter for quality
                    if not self._passes_basic_filter(row):
                        continue
                    
                    # Score by category priority
                    title_desc = f"{row.get('title', '')} {row.get('description', '')}".lower()
                    category_scores = {}
                    
                    for category, keywords in category_keywords.items():
                        score = sum(1 for keyword in keywords if keyword in title_desc)
                        if score > 0:
                            category_scores[category] = score
                    
                    if category_scores:
                        best_category = max(category_scores.items(), key=lambda x: x[1])
                        row['predicted_category'] = best_category[0]
                        row['category_confidence'] = best_category[1]
                        candidates.append(row)
                    
                    if len(candidates) >= limit:
                        break
            
            # Sort by quality indicators and category balance
            candidates.sort(key=lambda x: (
                x.get('category_confidence', 0),
                -int(x.get('parse_errors', 0)),
                int(x.get('newest_item_pubdate', 0))
            ), reverse=True)
            
            print(f"✅ Found {len(candidates)} strategic candidates")
            return candidates
            
        except Exception as e:
            print(f"❌ Error loading candidates: {e}")
            return []
    
    def _passes_basic_filter(self, row: Dict) -> bool:
        """Basic quality filter"""
        return (
            row.get('dead') == '0' and
            row.get('url', '').startswith(('http://', 'https://')) and
            len(row.get('title', '').strip()) > 3 and
            row.get('duplicateof') == 'NULL' and
            int(row.get('parse_errors', 0)) <= 8 and  # More lenient
            int(row.get('newest_item_pubdate', 0)) > 0
        )
    
    def calculate_quality_score(self, feed_data) -> float:
        """Enhanced quality scoring"""
        try:
            feed = feedparser.parse(feed_data['url'])
            
            if feed.bozo and not feed.entries:
                return 0
            
            score = 0
            
            # Episode count (max 20 points) - more generous
            episode_count = len(feed.entries)
            score += min(episode_count / 3, 20)  # Every 3 episodes = 1 point
            
            # Recent activity (max 25 points) - more lenient
            recent_count = 0
            cutoff = datetime.now() - timedelta(days=90)  # 3 months
            
            for entry in feed.entries[:15]:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date > cutoff:
                            recent_count += 1
                    except:
                        pass
            
            score += min(recent_count * 3, 25)  # More generous scoring
            
            # Metadata quality (max 25 points)
            if feed.feed.get('title'): score += 5
            if feed.feed.get('description'): score += 5
            if feed.feed.get('author'): score += 5
            if feed.feed.get('language'): score += 5
            if (hasattr(feed.feed, 'image') and feed.feed.image.get('href')) or feed.feed.get('logo'):
                score += 5
            
            # Episode metadata quality (max 20 points) - reduced weight
            metadata_score = 0
            for entry in feed.entries[:5]:
                if entry.get('title'): metadata_score += 1.5
                if entry.get('description') or entry.get('summary'): metadata_score += 1.5
                if hasattr(entry, 'enclosures') and entry.enclosures: metadata_score += 1
            
            score += min(metadata_score, 20)
            
            # Bonus points
            if feed_data.get('itunes_id'): score += 8
            if episode_count > 25: score += 5
            if episode_count > 100: score += 5
            
            # Category relevance bonus
            if feed_data.get('category_confidence', 0) >= 2: score += 5
            
            return round(score, 1)
            
        except Exception as e:
            return 0
    
    def validate_feed(self, candidate: Dict) -> Tuple[bool, Dict]:
        """Validate feed with enhanced categorization"""
        url = candidate['url']
        title = candidate.get('title', 'Unknown')
        
        print(f"  🔍 {title[:50]}...")
        
        try:
            # Quick connectivity check
            response = requests.head(url, timeout=8, allow_redirects=True)
            if response.status_code not in [200, 301, 302]:
                print(f"    ❌ HTTP {response.status_code}")
                return False, {}
            
            # Calculate quality score
            score = self.calculate_quality_score(candidate)
            
            if score < self.min_score:
                print(f"    ❌ Score: {score}")
                return False, {}
            
            # Parse for metadata
            feed = feedparser.parse(url)
            
            # Enhanced category extraction
            categories = self.extract_enhanced_categories(feed, candidate)
            
            feed_data = {
                'rss_url': url,
                'title': feed.feed.get('title', title),
                'categories': categories,
                'language': feed.feed.get('language', 'en'),
                'quality_score': score,
                'total_episodes': len(feed.entries),
                'predicted_category': candidate.get('predicted_category', 'General')
            }
            
            print(f"    ✅ Score: {score} | Episodes: {len(feed.entries)} | Category: {categories[0] if categories else 'Unknown'}")
            return True, feed_data
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:50]}")
            return False, {}
    
    def extract_enhanced_categories(self, feed, candidate: Dict) -> List[str]:
        """Enhanced category extraction with better mapping"""
        categories = []
        
        # Try iTunes categories first
        if hasattr(feed.feed, 'tags'):
            for tag in feed.feed.tags[:2]:
                if tag.get('term'):
                    # Map iTunes categories to our standard categories
                    itunes_cat = tag.term
                    mapped_cat = self.map_itunes_category(itunes_cat)
                    if mapped_cat:
                        categories.append(mapped_cat)
        
        # Use predicted category if no iTunes categories
        if not categories and candidate.get('predicted_category'):
            categories.append(candidate['predicted_category'])
        
        # Fallback to content analysis
        if not categories:
            content_cat = self.analyze_content_category(feed)
            if content_cat:
                categories.append(content_cat)
        
        # Ensure we have at least one category
        if not categories:
            categories.append('General')
        
        return categories[:2]  # Max 2 categories
    
    def map_itunes_category(self, itunes_cat: str) -> str:
        """Map iTunes categories to our standard categories"""
        mapping = {
            'Technology': 'Technology',
            'Business': 'Business', 
            'News': 'News',
            'Science': 'Science',
            'Comedy': 'Comedy',
            'Health & Fitness': 'Health',
            'Sports': 'Sports',
            'Education': 'Education',
            'True Crime': 'True Crime',
            'Music': 'Music',
            'Arts': 'Arts',
            'Government': 'Politics',
            'Society & Culture': 'Society',
            'History': 'History',
            'Religion & Spirituality': 'Religion',
            'TV & Film': 'Entertainment',
            'Leisure': 'Entertainment'
        }
        
        for key, value in mapping.items():
            if key.lower() in itunes_cat.lower():
                return value
        
        return None
    
    def analyze_content_category(self, feed) -> str:
        """Analyze content to determine category"""
        content = f"{feed.feed.get('title', '')} {feed.feed.get('description', '')}".lower()
        
        category_keywords = {
            'Technology': ['tech', 'programming', 'software', 'ai', 'startup', 'coding'],
            'Business': ['business', 'entrepreneur', 'marketing', 'finance', 'leadership'],
            'News': ['news', 'politics', 'current', 'journalism', 'daily'],
            'Science': ['science', 'research', 'physics', 'biology', 'space'],
            'Comedy': ['comedy', 'humor', 'funny', 'laugh', 'standup'],
            'Health': ['health', 'fitness', 'wellness', 'medical', 'nutrition'],
            'Sports': ['sports', 'football', 'basketball', 'baseball', 'soccer'],
            'Education': ['education', 'learning', 'teaching', 'university'],
            'True Crime': ['crime', 'murder', 'investigation', 'detective'],
            'Music': ['music', 'artist', 'album', 'song', 'musician'],
            'History': ['history', 'historical', 'ancient', 'war'],
            'Finance': ['finance', 'money', 'investing', 'stocks', 'crypto']
        }
        
        for category, keywords in category_keywords.items():
            if sum(1 for keyword in keywords if keyword in content) >= 2:
                return category
        
        return 'General'
    
    def process_candidates(self, candidates: List[Dict], target_new: int = 70) -> List[Dict]:
        """Process candidates with category balancing"""
        validated = []
        processed = 0
        category_counts = defaultdict(int)
        
        # Get existing URLs to avoid duplicates
        existing_urls = {feed['rss_url'].lower() for feed in self.existing_feeds}
        
        print(f"\n🔄 Processing candidates (target: {target_new} new feeds)")
        print(f"📊 Quality threshold: {self.min_score}+ points")
        
        for candidate in candidates:
            if len(validated) >= target_new:
                break
                
            url = candidate['url'].lower()
            if url in existing_urls:
                continue
            
            processed += 1
            is_valid, feed_data = self.validate_feed(candidate)
            
            if is_valid:
                # Check category balance
                primary_category = feed_data.get('categories', ['General'])[0]
                max_for_category = self.target_categories.get(primary_category, 3)
                
                if category_counts[primary_category] < max_for_category:
                    validated.append(feed_data)
                    category_counts[primary_category] += 1
                    existing_urls.add(url)
                    
                    if len(validated) % 10 == 0:
                        print(f"  📊 Progress: {len(validated)} validated, {processed} processed")
                        print(f"      Categories: {dict(category_counts)}")
            
            # Be respectful to servers
            time.sleep(1.5)
        
        return validated
    
    def merge_and_save(self, new_feeds: List[Dict], output_file: str = 'feeds_100plus.json'):
        """Merge and save 100+ feeds"""
        # Sort new feeds by quality score
        new_feeds.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # Merge with existing
        all_feeds = self.existing_feeds.copy()
        
        for feed in new_feeds:
            clean_feed = {
                'rss_url': feed['rss_url'],
                'title': feed['title'],
                'categories': feed['categories'],
                'language': feed['language']
            }
            all_feeds.append(clean_feed)
        
        # Save
        with open(output_file, 'w') as f:
            json.dump(all_feeds, f, indent=2)
        
        print(f"\n✅ Saved {len(all_feeds)} total feeds to {output_file}")
        
        # Show category distribution
        category_counts = defaultdict(int)
        for feed in all_feeds:
            for cat in feed.get('categories', []):
                category_counts[cat] += 1
        
        print(f"\n📊 Final Category Distribution:")
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cat}: {count}")
        
        return all_feeds

def main():
    """Scale to 100+ premium feeds"""
    print("🚀 Scaling to 100+ Premium Podcast Feeds")
    print("=" * 60)
    
    scaler = PremiumScaler(min_score=55)  # Slightly lower for diversity
    
    # Load existing feeds and analyze
    existing = scaler.load_existing_feeds()
    
    # Get strategic candidates
    print(f"\n🎯 Target: Add 70+ feeds for 100+ total")
    candidates = scaler.get_strategic_candidates(limit=1000)  # Process more candidates
    
    if not candidates:
        print("❌ No candidates found")
        return
    
    # Process candidates with category balancing
    target_new_feeds = 70
    validated = scaler.process_candidates(candidates, target_new_feeds)
    
    print(f"\n🎯 Scaling Results:")
    print(f"  📊 Candidates processed: {len(candidates)}")
    print(f"  ✅ New feeds validated: {len(validated)}")
    print(f"  📈 Success rate: {len(validated)/min(len(candidates), 100)*100:.1f}%")
    
    if validated:
        # Show top feeds by category
        print(f"\n🏆 New Feeds by Category:")
        category_feeds = defaultdict(list)
        for feed in validated:
            category = feed.get('categories', ['General'])[0]
            category_feeds[category].append(feed)
        
        for category, feeds in sorted(category_feeds.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  📂 {category}: {len(feeds)} feeds")
            for feed in feeds[:3]:  # Show top 3 per category
                score = feed.get('quality_score', 0)
                episodes = feed.get('total_episodes', 0)
                print(f"     • {feed['title'][:40]} (Score: {score}, Episodes: {episodes})")
        
        # Merge and save
        final_feeds = scaler.merge_and_save(validated)
        
        print(f"\n📝 Final Summary:")
        print(f"  🎙️ Previous feeds: {len(existing)}")
        print(f"  ➕ New feeds added: {len(validated)}")
        print(f"  📊 Total feeds: {len(final_feeds)}")
        print(f"\n🎉 Ready for 100+ feed system!")
        print(f"💡 Review feeds_100plus.json and replace feeds.json when ready")
    else:
        print("\n❌ No feeds met criteria")

if __name__ == "__main__":
    main()