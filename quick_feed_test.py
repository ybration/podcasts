#!/usr/bin/env python3
"""
Quick test of RSS feed expansion
"""

import csv
import json

def main():
    # Load existing feeds
    with open('feeds.json', 'r') as f:
        existing = json.load(f)
    print(f"Existing feeds: {len(existing)}")
    
    # Load podcastindex data
    feeds = []
    with open('podcastindex-db/db_newsfeeds_1000rows.csv', 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 20:  # Just first 20 for testing
                break
            
            # Basic filtering
            if (row.get('dead') == '0' and 
                row.get('url', '').startswith(('http://', 'https://')) and
                row.get('title', '').strip() and
                row.get('duplicateof') == 'NULL'):
                
                feeds.append({
                    'rss_url': row['url'],
                    'title': row['title'],
                    'categories': ['General'],  # Default category
                    'language': 'en'
                })
    
    print(f"Filtered feeds: {len(feeds)}")
    
    # Show sample feeds
    print("\nSample feeds:")
    for i, feed in enumerate(feeds[:5]):
        print(f"  {i+1}. {feed['title']}")
        print(f"     {feed['rss_url']}")
    
    # Merge with existing (avoid duplicates by URL)
    existing_urls = {f['rss_url'].lower() for f in existing}
    new_feeds = [f for f in feeds if f['rss_url'].lower() not in existing_urls]
    
    print(f"\nNew feeds (not duplicates): {len(new_feeds)}")
    
    # Combine
    all_feeds = existing + new_feeds[:10]  # Add max 10 new feeds
    
    # Save
    with open('feeds_test.json', 'w') as f:
        json.dump(all_feeds, f, indent=2)
    
    print(f"Total feeds: {len(all_feeds)}")
    print("Saved to feeds_test.json")

if __name__ == "__main__":
    main()