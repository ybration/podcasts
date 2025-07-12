#!/usr/bin/env python3
"""
Quick 100+ Feed Expansion
Fast approach using metadata filtering before RSS validation
"""

import csv
import json
import random
from collections import defaultdict

def analyze_current_feeds():
    """Analyze current feed distribution"""
    with open('feeds.json', 'r') as f:
        feeds = json.load(f)
    
    print(f"📊 Current feeds: {len(feeds)}")
    
    # Count categories
    category_count = defaultdict(int)
    for feed in feeds:
        for cat in feed.get('categories', []):
            category_count[cat] += 1
    
    print("Current categories:")
    for cat, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")
    
    return feeds, category_count

def get_quality_candidates():
    """Get quality candidates using smart filtering"""
    candidates = []
    
    # Define quality filters
    quality_keywords = [
        'technology', 'business', 'news', 'science', 'comedy', 'health', 
        'sports', 'education', 'history', 'music', 'finance', 'startup',
        'programming', 'entrepreneur', 'politics', 'culture', 'art',
        'podcast', 'show', 'talk', 'radio', 'weekly', 'daily'
    ]
    
    try:
        with open('podcastindex-db/db_newsfeeds_1000rows.csv', 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Basic quality filter
                if (row.get('dead') == '0' and 
                    row.get('url', '').startswith(('http://', 'https://')) and
                    len(row.get('title', '').strip()) > 5 and
                    row.get('duplicateof') == 'NULL' and
                    int(row.get('parse_errors', 0)) <= 5):
                    
                    # Content quality filter
                    title_desc = f"{row.get('title', '')} {row.get('description', '')}".lower()
                    quality_score = sum(1 for keyword in quality_keywords if keyword in title_desc)
                    
                    if quality_score >= 2:  # At least 2 quality keywords
                        row['quality_score'] = quality_score
                        candidates.append(row)
        
        # Sort by quality indicators
        candidates.sort(key=lambda x: (
            x.get('quality_score', 0),
            -int(x.get('parse_errors', 0)),
            int(x.get('newest_item_pubdate', 0))
        ), reverse=True)
        
        print(f"✅ Found {len(candidates)} quality candidates")
        return candidates
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def categorize_feed(row):
    """Categorize feed based on title and description"""
    content = f"{row.get('title', '')} {row.get('description', '')}".lower()
    
    # Category keyword mapping
    categories = {
        'Technology': ['tech', 'programming', 'software', 'ai', 'startup', 'coding', 'developer', 'digital'],
        'Business': ['business', 'entrepreneur', 'marketing', 'finance', 'leadership', 'startup', 'company'],
        'News': ['news', 'politics', 'current', 'journalism', 'daily', 'weekly', 'report'],
        'Science': ['science', 'research', 'physics', 'biology', 'chemistry', 'space', 'nature'],
        'Comedy': ['comedy', 'humor', 'funny', 'laugh', 'standup', 'improv', 'joke'],
        'Health': ['health', 'fitness', 'wellness', 'medical', 'nutrition', 'mental', 'therapy'],
        'Sports': ['sports', 'football', 'basketball', 'baseball', 'soccer', 'fitness', 'athletic'],
        'Education': ['education', 'learning', 'teaching', 'university', 'academic', 'school'],
        'Music': ['music', 'artist', 'album', 'song', 'musician', 'band', 'audio'],
        'True Crime': ['crime', 'murder', 'investigation', 'detective', 'mystery', 'police'],
        'History': ['history', 'historical', 'ancient', 'war', 'past', 'civilization'],
        'Finance': ['finance', 'money', 'investing', 'stocks', 'crypto', 'economy', 'wealth'],
        'Entertainment': ['tv', 'film', 'movie', 'entertainment', 'celebrity', 'show', 'review'],
        'Religion': ['religion', 'spiritual', 'faith', 'church', 'god', 'bible', 'prayer'],
        'Society': ['society', 'culture', 'social', 'community', 'people', 'life']
    }
    
    # Score each category
    category_scores = {}
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in content)
        if score > 0:
            category_scores[category] = score
    
    if category_scores:
        best_category = max(category_scores.items(), key=lambda x: x[1])
        return best_category[0]
    
    return 'General'

def select_balanced_feeds(candidates, current_feeds, target_total=100):
    """Select feeds to create balanced 100+ feed collection"""
    
    # Target distribution for 100 feeds
    target_distribution = {
        'Technology': 15,
        'Business': 12,
        'News': 10,
        'Science': 8,
        'Comedy': 8,
        'Health': 6,
        'Sports': 6,
        'Education': 5,
        'Music': 5,
        'Entertainment': 5,
        'Finance': 4,
        'True Crime': 4,
        'History': 3,
        'Religion': 3,
        'Society': 3,
        'General': 3
    }
    
    # Count current categories
    current_counts = defaultdict(int)
    for feed in current_feeds:
        for cat in feed.get('categories', []):
            current_counts[cat] += 1
    
    # Calculate needed feeds per category
    needed_per_category = {}
    for category, target in target_distribution.items():
        current = current_counts.get(category, 0)
        needed = max(0, target - current)
        needed_per_category[category] = needed
    
    print("\n📋 Needed feeds per category:")
    for cat, needed in sorted(needed_per_category.items(), key=lambda x: x[1], reverse=True):
        current = current_counts.get(cat, 0)
        target = target_distribution.get(cat, 0)
        print(f"  {cat}: {needed} needed (current: {current}, target: {target})")
    
    # Group candidates by category
    candidates_by_category = defaultdict(list)
    for candidate in candidates:
        category = categorize_feed(candidate)
        candidates_by_category[category].append(candidate)
    
    # Select feeds to balance categories
    selected_feeds = []
    existing_urls = {feed['rss_url'].lower() for feed in current_feeds}
    
    for category, needed in needed_per_category.items():
        if needed > 0 and category in candidates_by_category:
            category_candidates = candidates_by_category[category]
            
            # Select top candidates from this category
            selected_count = 0
            for candidate in category_candidates:
                if selected_count >= needed:
                    break
                
                url = candidate['url'].lower()
                if url not in existing_urls:
                    # Create feed entry
                    feed_entry = {
                        'rss_url': candidate['url'],
                        'title': candidate['title'],
                        'categories': [category],
                        'language': 'en'  # Default to English
                    }
                    
                    selected_feeds.append(feed_entry)
                    existing_urls.add(url)
                    selected_count += 1
                    
                    print(f"  ✅ Selected: {candidate['title'][:50]} → {category}")
    
    return selected_feeds

def main():
    """Quick expansion to 100+ feeds"""
    print("🚀 Quick Expansion to 100+ Premium Feeds")
    print("=" * 50)
    
    # Analyze current feeds
    current_feeds, current_categories = analyze_current_feeds()
    
    # Get quality candidates
    candidates = get_quality_candidates()
    
    if not candidates:
        print("❌ No candidates found")
        return
    
    # Select balanced feeds
    print(f"\n🎯 Selecting feeds for balanced 100+ collection...")
    new_feeds = select_balanced_feeds(candidates, current_feeds, target_total=100)
    
    if new_feeds:
        # Merge with existing
        all_feeds = current_feeds + new_feeds
        
        # Save to new file
        with open('feeds_100plus.json', 'w') as f:
            json.dump(all_feeds, f, indent=2)
        
        print(f"\n📝 Results:")
        print(f"  🎙️ Previous feeds: {len(current_feeds)}")
        print(f"  ➕ New feeds added: {len(new_feeds)}")
        print(f"  📊 Total feeds: {len(all_feeds)}")
        
        # Show new category distribution
        final_categories = defaultdict(int)
        for feed in all_feeds:
            for cat in feed.get('categories', []):
                final_categories[cat] += 1
        
        print(f"\n📊 Final Category Distribution:")
        for cat, count in sorted(final_categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cat}: {count}")
        
        print(f"\n✅ Saved to feeds_100plus.json")
        print(f"💡 Review and replace feeds.json when ready!")
        
        # Show sample of new feeds
        print(f"\n🆕 Sample New Feeds:")
        for i, feed in enumerate(new_feeds[:10], 1):
            category = feed['categories'][0] if feed['categories'] else 'General'
            print(f"  {i:2d}. {feed['title'][:45]} → {category}")
        
        if len(new_feeds) > 10:
            print(f"     ... and {len(new_feeds) - 10} more feeds")
    
    else:
        print("❌ No suitable feeds found for expansion")

if __name__ == "__main__":
    main()