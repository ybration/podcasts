#!/usr/bin/env python3
"""
High-Quality RSS Feed Expansion
Adds premium podcast feeds with quality scoring
"""

import csv
import json
import feedparser
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class QualityFeedExpander:
    """Expand feeds with quality validation"""
    
    def __init__(self, min_score: int = 60):
        self.min_score = min_score
        self.existing_feeds = []
        self.validated_feeds = []
        
    def load_existing_feeds(self) -> List[Dict]:
        """Load current feeds.json"""
        try:
            with open('feeds.json', 'r') as f:
                self.existing_feeds = json.load(f)
            print(f"✅ Loaded {len(self.existing_feeds)} existing feeds")
            return self.existing_feeds
        except FileNotFoundError:
            print("❌ feeds.json not found")
            return []
    
    def get_quality_candidates(self, limit: int = 100) -> List[Dict]:
        """Get high-quality candidates from Podcastindex"""
        candidates = []
        
        try:
            with open('podcastindex-db/db_newsfeeds_1000rows.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Pre-filter for quality indicators
                    if (row.get('dead') == '0' and 
                        row.get('url', '').startswith(('http://', 'https://')) and
                        row.get('title', '').strip() and
                        row.get('duplicateof') == 'NULL' and
                        int(row.get('parse_errors', 0)) <= 5 and
                        row.get('itunes_id') and  # Has iTunes presence
                        int(row.get('newest_item_pubdate', 0)) > 0):  # Has episode data
                        
                        candidates.append(row)
                        
                        if len(candidates) >= limit:
                            break
            
            print(f"✅ Found {len(candidates)} quality candidates")
            return candidates
            
        except Exception as e:
            print(f"❌ Error loading candidates: {e}")
            return []
    
    def calculate_quality_score(self, feed_data) -> float:
        """Calculate quality score from feed data"""
        try:
            feed = feedparser.parse(feed_data['url'])
            
            if feed.bozo and not feed.entries:
                return 0
            
            score = 0
            
            # Episode count (max 20 points)
            episode_count = len(feed.entries)
            score += min(episode_count / 5, 20)  # More generous scoring
            
            # Recent activity (max 25 points)
            recent_count = 0
            cutoff = datetime.now() - timedelta(days=60)  # More lenient - 2 months
            
            for entry in feed.entries[:10]:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date > cutoff:
                            recent_count += 1
                    except:
                        pass
            
            score += min(recent_count * 5, 25)
            
            # Metadata quality (max 25 points)
            if feed.feed.get('title'): score += 5
            if feed.feed.get('description'): score += 5
            if feed.feed.get('author'): score += 5
            if feed.feed.get('language'): score += 5
            if (hasattr(feed.feed, 'image') and feed.feed.image.get('href')) or feed.feed.get('logo'):
                score += 5
            
            # Episode metadata quality (max 30 points)
            metadata_score = 0
            for entry in feed.entries[:5]:
                if entry.get('title'): metadata_score += 2
                if entry.get('description') or entry.get('summary'): metadata_score += 2
                if hasattr(entry, 'enclosures') and entry.enclosures: metadata_score += 2
            
            score += min(metadata_score, 30)
            
            # Bonus points for quality indicators
            if feed_data.get('itunes_id'): score += 10  # iTunes presence
            if episode_count > 50: score += 5  # Established podcast
            
            return round(score, 1)
            
        except Exception as e:
            print(f"    ❌ Error calculating score: {e}")
            return 0
    
    def validate_feed(self, candidate: Dict) -> Tuple[bool, Dict]:
        """Validate a single feed and return quality data"""
        url = candidate['url']
        title = candidate.get('title', 'Unknown')
        
        print(f"  🔍 Validating: {title}")
        
        try:
            # Quick connectivity check
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                print(f"    ❌ HTTP {response.status_code}")
                return False, {}
            
            # Calculate quality score
            score = self.calculate_quality_score(candidate)
            
            if score < self.min_score:
                print(f"    ❌ Low score: {score}")
                return False, {}
            
            # Parse for metadata
            feed = feedparser.parse(url)
            
            # Extract categories
            categories = self.extract_categories(feed, candidate)
            
            feed_data = {
                'rss_url': url,
                'title': feed.feed.get('title', title),
                'categories': categories,
                'language': feed.feed.get('language', 'en'),
                'quality_score': score,
                'total_episodes': len(feed.entries),
                'description': feed.feed.get('description', '')[:100]  # Truncate
            }
            
            print(f"    ✅ Score: {score} | Episodes: {len(feed.entries)} | Categories: {categories}")
            return True, feed_data
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return False, {}
    
    def extract_categories(self, feed, candidate: Dict) -> List[str]:
        """Extract categories from feed or infer from content"""
        categories = []
        
        # Try iTunes categories first
        if hasattr(feed.feed, 'tags'):
            for tag in feed.feed.tags[:3]:  # Limit to 3
                if tag.get('term'):
                    categories.append(tag.term)
        
        # Fallback to content-based categorization
        if not categories:
            title = feed.feed.get('title', '').lower()
            description = feed.feed.get('description', '').lower()
            content = f"{title} {description}"
            
            if any(word in content for word in ['tech', 'technology', 'programming', 'software', 'ai', 'computer']):
                categories.append('Technology')
            elif any(word in content for word in ['news', 'politics', 'current events', 'journalism']):
                categories.append('News')
            elif any(word in content for word in ['business', 'entrepreneur', 'finance', 'startup', 'money']):
                categories.append('Business')
            elif any(word in content for word in ['science', 'research', 'education', 'learning']):
                categories.append('Science')
            elif any(word in content for word in ['comedy', 'humor', 'funny', 'laugh']):
                categories.append('Comedy')
            elif any(word in content for word in ['health', 'fitness', 'wellness', 'medical']):
                categories.append('Health')
            elif any(word in content for word in ['history', 'culture', 'society', 'documentary']):
                categories.append('Society & Culture')
            elif any(word in content for word in ['sports', 'football', 'basketball', 'baseball']):
                categories.append('Sports')
            else:
                categories.append('General')
        
        return categories[:2]  # Max 2 categories
    
    def process_candidates(self, candidates: List[Dict], target_count: int = 25) -> List[Dict]:
        """Process candidates and return validated feeds"""
        validated = []
        processed = 0
        
        # Get existing URLs to avoid duplicates
        existing_urls = {feed['rss_url'].lower() for feed in self.existing_feeds}
        
        print(f"\n🔄 Processing candidates (target: {target_count} new feeds)")
        print(f"📊 Quality threshold: {self.min_score}+ points")
        
        for candidate in candidates:
            if len(validated) >= target_count:
                break
                
            url = candidate['url'].lower()
            if url in existing_urls:
                print(f"  ⏭️  Skipping duplicate: {candidate.get('title', url)}")
                continue
            
            processed += 1
            is_valid, feed_data = self.validate_feed(candidate)
            
            if is_valid:
                validated.append(feed_data)
                existing_urls.add(url)  # Prevent duplicates within this session
            
            # Be respectful to servers
            time.sleep(2)
            
            if processed % 10 == 0:
                print(f"  📊 Progress: {len(validated)} validated, {processed} processed")
        
        return validated
    
    def merge_and_save(self, new_feeds: List[Dict], output_file: str = 'feeds_expanded.json'):
        """Merge with existing feeds and save"""
        # Sort new feeds by quality score (highest first)
        new_feeds.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # Merge
        all_feeds = self.existing_feeds.copy()
        
        for feed in new_feeds:
            # Remove quality_score and other internal fields before saving
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
        return all_feeds

def main():
    """Main expansion process"""
    print("🎙️ High-Quality RSS Feed Expansion")
    print("=" * 50)
    
    # Initialize expander with quality threshold
    expander = QualityFeedExpander(min_score=60)  # Premium feeds only
    
    # Load existing feeds
    existing = expander.load_existing_feeds()
    
    # Get quality candidates
    candidates = expander.get_quality_candidates(limit=200)  # Process more to find quality ones
    
    if not candidates:
        print("❌ No candidates found")
        return
    
    # Process and validate
    target_new_feeds = 25  # Add 25 high-quality feeds
    validated = expander.process_candidates(candidates, target_new_feeds)
    
    print(f"\n🎯 Validation Results:")
    print(f"  📊 Candidates processed: {len(candidates)}")
    print(f"  ✅ Feeds validated: {len(validated)}")
    print(f"  📈 Success rate: {len(validated)/min(len(candidates), 50)*100:.1f}%")
    
    if validated:
        # Show top feeds by score
        print(f"\n🏆 Top Quality Feeds Added:")
        for i, feed in enumerate(validated[:10], 1):
            score = feed.get('quality_score', 0)
            episodes = feed.get('total_episodes', 0)
            categories = ', '.join(feed.get('categories', []))
            print(f"  {i:2d}. {feed['title']} (Score: {score}, Episodes: {episodes}, Categories: {categories})")
        
        # Merge and save
        final_feeds = expander.merge_and_save(validated)
        
        print(f"\n📝 Summary:")
        print(f"  🎙️ Previous feeds: {len(existing)}")
        print(f"  ➕ New feeds added: {len(validated)}")
        print(f"  📊 Total feeds: {len(final_feeds)}")
        print(f"\n🎉 Ready to update feeds.json!")
        print(f"💡 Review feeds_expanded.json and replace feeds.json when ready")
    else:
        print("\n❌ No feeds met quality criteria")
        print("💡 Try lowering min_score or checking different candidates")

if __name__ == "__main__":
    main()