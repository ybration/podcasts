# 🔄 Complete System Flow Simulation

Let me walk you through exactly how data flows from GitHub Actions → Supabase → Mobile Device.

## 🕐 Step-by-Step Flow

### 📅 **Daily Trigger (6:00 AM UTC)**

```yaml
# .github/workflows/update-podcasts.yml triggers
schedule:
  - cron: '0 6 * * *'  # Every day at 6 AM UTC
```

**What happens:**
- GitHub's scheduler wakes up the workflow
- Spins up an Ubuntu virtual machine
- Starts executing the workflow steps

---

### 🐍 **Step 1: Environment Setup**

```bash
# GitHub Actions VM runs:
- uses: actions/checkout@v4        # Downloads your repo files
- uses: actions/setup-python@v4    # Installs Python 3.11
- run: pip install -r requirements.txt  # Installs feedparser, requests
```

**Result:** 
- VM has Python + dependencies
- Has access to `feeds.json` and `update_podcasts.py`

---

### 📡 **Step 2: Script Execution with Secrets**

```bash
# Environment variables injected from GitHub Secrets:
SUPABASE_URL=https://pmijctxikafxsqdqxdej.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ0eXAiOiJKV1QiLCJhb... (your secret key)

# Script starts:
python update_podcasts.py
```

---

### 📰 **Step 3: RSS Feed Processing**

**Script loads feeds.json:**
```json
[
  {
    "rss_url": "https://feeds.npr.org/510289/podcast.xml",
    "title": "Planet Money", 
    "categories": ["Business", "Economics", "News"]
  }
  // ... 4 more podcasts
]
```

**For each podcast:**

1. **HTTP Request to RSS Feed:**
```python
# Script makes HTTP request:
feed = feedparser.parse("https://feeds.npr.org/510289/podcast.xml")
```

2. **RSS Server Response (XML):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Planet Money</title>
    <description>Economy podcast by NPR</description>
    <image>
      <url>https://media.npr.org/podcast-image.jpg</url>
    </image>
    <item>
      <title>Made in America</title>
      <description>Episode about manufacturing</description>
      <pubDate>Fri, 11 Jul 2025 22:25:07 +0000</pubDate>
      <enclosure url="https://play.podtrac.com/audio.mp3" type="audio/mpeg"/>
    </item>
    <!-- ... more episodes -->
  </channel>
</rss>
```

3. **Script Extracts Metadata:**
```python
podcast_data = {
    'rss_url': 'https://feeds.npr.org/510289/podcast.xml',
    'title': 'Planet Money',
    'description': 'Economy podcast by NPR', 
    'image_url': 'https://media.npr.org/podcast-image.jpg',
    'categories': ['Business', 'Economics', 'News'],
    'total_episodes': 355,
    'latest_episode_date': '2025-07-11T22:25:07+00:00'
}
```

---

### 🗄️ **Step 4: Data Upload to Supabase**

**Podcast Upload:**
```python
# Script makes HTTPS POST to Supabase:
POST https://pmijctxikafxsqdqxdej.supabase.co/rest/v1/podcasts
Headers:
  Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhb...
  Content-Type: application/json

Body:
{
  "rss_url": "https://feeds.npr.org/510289/podcast.xml",
  "title": "Planet Money",
  "description": "Economy podcast by NPR",
  "categories": ["Business", "Economics", "News"],
  "image_url": "https://media.npr.org/podcast-image.jpg",
  "total_episodes": 355,
  "latest_episode_date": "2025-07-11T22:25:07+00:00"
}
```

**Supabase Response:**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "created_at": "2025-07-12T06:15:23.123456+00:00"
}
```

**Episode Upload (for each episode):**
```python
# Script gets podcast ID, then uploads episodes:
POST https://pmijctxikafxsqdqxdej.supabase.co/rest/v1/episodes

Body:
{
  "podcast_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "Made in America",
  "description": "Episode about manufacturing",
  "published_at": "2025-07-11T22:25:07+00:00",
  "audio_url": "https://play.podtrac.com/audio.mp3",
  "duration": 1680
}
```

---

### 📊 **Step 5: Database Storage**

**Supabase PostgreSQL stores:**

**podcasts table:**
```sql
id                  | f47ac10b-58cc-4372-a567-0e02b2c3d479
rss_url            | https://feeds.npr.org/510289/podcast.xml  
title              | Planet Money
description        | Economy podcast by NPR
categories         | {Business,Economics,News}
image_url          | https://media.npr.org/podcast-image.jpg
total_episodes     | 355
latest_episode_date| 2025-07-11 22:25:07+00:00
created_at         | 2025-07-12 06:15:23.123456+00:00
```

**episodes table:**
```sql
id         | a1b2c3d4-e5f6-7890-1234-567890abcdef
podcast_id | f47ac10b-58cc-4372-a567-0e02b2c3d479
title      | Made in America  
description| Episode about manufacturing
published_at| 2025-07-11 22:25:07+00:00
audio_url  | https://play.podtrac.com/audio.mp3
duration   | 1680
created_at | 2025-07-12 06:15:25.456789+00:00
```

---

### ✅ **Step 6: GitHub Actions Completion**

```bash
# Workflow finishes successfully:
✓ Install dependencies
✓ Run podcast update script  
✓ Process 5 podcasts
✓ Upload 247 episodes
✓ Workflow completed in 2m 34s
```

**GitHub Actions Log:**
```
2025-07-12T06:15:20.123Z INFO Processing podcast 1/5
2025-07-12T06:15:21.456Z INFO Successfully processed Planet Money
2025-07-12T06:15:22.789Z INFO Successfully processed 52 episodes for Planet Money
2025-07-12T06:15:23.012Z INFO Processing podcast 2/5
...
2025-07-12T06:17:45.678Z INFO Completed processing. Successfully updated 5/5 podcasts
```

---

## 📱 **Mobile Device Data Fetching**

### **User Opens Podcast App**

**App connects to Supabase:**
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://pmijctxikafxsqdqxdej.supabase.co',
  'eyJ0eXAiOiJKV1QiLCJhb... (anon key, not service role)'
)
```

---

### **Scenario 1: Browse Recent Podcasts**

**App makes query:**
```javascript
const { data } = await supabase
  .from('podcasts')
  .select('*')
  .order('latest_episode_date', { ascending: false })
  .limit(10)
```

**Supabase SQL executed:**
```sql
SELECT * FROM podcasts 
ORDER BY latest_episode_date DESC 
LIMIT 10;
```

**Response to app:**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "title": "Planet Money",
    "description": "Economy podcast by NPR",
    "image_url": "https://media.npr.org/podcast-image.jpg",
    "categories": ["Business", "Economics", "News"],
    "latest_episode_date": "2025-07-11T22:25:07+00:00"
  }
  // ... more podcasts
]
```

**App displays:** List of podcast cards with images and titles

---

### **Scenario 2: Search for "Technology" Podcasts**

**User types "technology" in search:**

**App makes query:**
```javascript
const { data } = await supabase
  .from('podcasts')
  .select('*')
  .contains('categories', ['Technology'])
```

**Supabase SQL executed:**
```sql
SELECT * FROM podcasts 
WHERE 'Technology' = ANY(categories);
```

**Response:** All podcasts tagged with "Technology"

---

### **Scenario 3: Get Episodes for a Podcast**

**User taps on "Planet Money":**

**App makes query:**
```javascript
const { data } = await supabase
  .from('episodes')
  .select(`
    *,
    podcasts!inner(title, image_url)
  `)
  .eq('podcast_id', 'f47ac10b-58cc-4372-a567-0e02b2c3d479')
  .order('published_at', { ascending: false })
  .limit(20)
```

**Supabase SQL executed:**
```sql
SELECT 
  episodes.*,
  podcasts.title as podcast_title,
  podcasts.image_url as podcast_image
FROM episodes 
JOIN podcasts ON episodes.podcast_id = podcasts.id
WHERE episodes.podcast_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479'
ORDER BY episodes.published_at DESC 
LIMIT 20;
```

**Response to app:**
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "title": "Made in America",
    "description": "Episode about manufacturing",
    "audio_url": "https://play.podtrac.com/audio.mp3",
    "published_at": "2025-07-11T22:25:07+00:00",
    "duration": 1680,
    "podcasts": {
      "title": "Planet Money",
      "image_url": "https://media.npr.org/podcast-image.jpg"
    }
  }
  // ... more episodes
]
```

**App displays:** Episode list with play buttons

---

### **Scenario 4: Full-Text Search**

**User searches "climate change":**

**App makes query:**
```javascript
const { data } = await supabase
  .from('episodes')
  .select(`
    *,
    podcasts!inner(title)
  `)
  .textSearch('title,description', 'climate & change')
  .limit(20)
```

**Supabase SQL executed:**
```sql
SELECT 
  episodes.*,
  podcasts.title as podcast_title
FROM episodes 
JOIN podcasts ON episodes.podcast_id = podcasts.id
WHERE to_tsvector('english', episodes.title || ' ' || episodes.description) 
      @@ plainto_tsquery('english', 'climate change')
ORDER BY ts_rank(
  to_tsvector('english', episodes.title || ' ' || episodes.description),
  plainto_tsquery('english', 'climate change')
) DESC
LIMIT 20;
```

**Response:** Episodes ranked by relevance to "climate change"

---

## 🔄 **Daily Update Cycle**

**What happens every day:**

1. **6:00 AM UTC**: GitHub Actions triggers
2. **6:01 AM**: Script fetches fresh RSS data
3. **6:02 AM**: New episodes get added to database
4. **6:03 AM**: Podcast metadata gets updated
5. **6:04 AM**: Workflow completes
6. **Immediately**: Mobile apps worldwide have access to fresh data

**Database changes:**
- New episodes appear automatically
- Podcast metadata stays current
- No app updates needed
- Zero downtime

---

## 🚀 **Performance & Scale**

**Current capacity:**
- **Podcasts**: 100 feeds
- **Episodes**: 5,000 total (50 per podcast)
- **Update time**: ~2-3 minutes
- **Database size**: ~50MB
- **Query speed**: <100ms average

**Mobile app benefits:**
- No backend API to maintain
- Direct database connection
- Real-time data access
- Built-in search and filtering
- Automatic scaling with Supabase

---

This system runs completely autonomously - fresh podcast data flows from RSS feeds → GitHub Actions → Supabase → Your mobile app, every single day! 🎉