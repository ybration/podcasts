# 🎙️ Podcast Metadata System

A simple podcast backend system that automatically fetches and stores podcast metadata from RSS feeds using GitHub Actions and Supabase.

## 🏗️ Architecture

- **GitHub Repository**: Stores RSS feed URLs and automation scripts
- **GitHub Actions**: Runs daily to fetch and parse RSS feeds  
- **Supabase**: Stores podcast and episode metadata in a queryable database
- **Mobile App**: Connects directly to Supabase for podcast discovery

## 📁 Project Structure

```
podcast-rss/
├── feeds.json                    # Hand-maintained list of podcast RSS URLs
├── update_podcasts.py           # Main script for RSS parsing and data upload
├── requirements.txt             # Python dependencies
├── supabase_schema.sql         # Database schema for Supabase
├── .github/workflows/
│   └── update-podcasts.yml     # GitHub Actions workflow
└── README.md                   # This file
```

## 🚀 Setup Instructions

### 1. Supabase Setup

Your Supabase project URL is: `https://pmijctxikafxsqdqxdej.supabase.co`

1. Go to your [Supabase project dashboard](https://supabase.com/dashboard/project/pmijctxikafxsqdqxdej)
2. Navigate to the SQL Editor and run the contents of `supabase_schema.sql`
3. Go to Settings > API and copy your service role API key

### 2. GitHub Repository Setup

1. Fork or create a new repository with these files
2. Go to Settings > Secrets and variables > Actions
3. Add the following repository secrets:
   - `SUPABASE_URL`: `https://pmijctxikafxsqdqxdej.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY`: Your service role key from Supabase Settings > API

### 3. Customize Podcast Feeds

Edit `feeds.json` to add your desired podcast RSS feeds:

```json
[
  {
    "rss_url": "https://feeds.example.com/podcast.xml",
    "title": "Example Podcast",
    "categories": ["Technology", "Education"],
    "language": "en",
    "country": "US"
  }
]
```

### 4. Test the Setup

You can manually trigger the workflow to test:
1. Go to Actions tab in your GitHub repository
2. Select "Update Podcast Metadata" workflow
3. Click "Run workflow"

## 📊 Database Schema

### Podcasts Table
- `id`: UUID primary key
- `rss_url`: RSS feed URL (unique)
- `title`: Podcast title
- `description`: Podcast description
- `author`: Publisher/owner name
- `language`: Language code (e.g., "en")
- `image_url`: Podcast artwork URL
- `categories`: Array of category strings
- `is_explicit`: Boolean flag
- `country`: Country code
- `total_episodes`: Episode count
- `latest_episode_date`: Most recent episode date
- `created_at`/`updated_at`: Timestamps

### Episodes Table
- `id`: UUID primary key
- `podcast_id`: Foreign key to podcasts table
- `title`: Episode title
- `description`: Episode description
- `published_at`: Publication date
- `duration`: Duration in seconds
- `audio_url`: Link to audio file
- `episode_type`: "full", "trailer", or "bonus"
- `season_number`/`episode_number`: Optional numbering
- `is_explicit`: Boolean flag
- `image_url`: Episode-specific artwork
- `created_at`/`updated_at`: Timestamps

## 🔄 How It Works

1. **Schedule**: GitHub Actions runs daily at 6:00 AM UTC
2. **Fetch**: Script loads RSS URLs from `feeds.json`
3. **Parse**: Each RSS feed is parsed using the `feedparser` library
4. **Extract**: Podcast and episode metadata is extracted
5. **Upload**: Data is sent to Supabase via REST API
6. **Limit**: Only the latest 50 episodes per podcast are stored

## 🔍 Querying Data

Your mobile app can query Supabase directly using SQL or the auto-generated REST API:

```sql
-- Search podcasts by keyword
SELECT * FROM podcasts 
WHERE to_tsvector('english', title || ' ' || description) @@ plainto_tsquery('technology');

-- Get recent episodes
SELECT e.*, p.title as podcast_title 
FROM episodes e 
JOIN podcasts p ON e.podcast_id = p.id 
ORDER BY e.published_at DESC 
LIMIT 20;

-- Filter by category
SELECT * FROM podcasts 
WHERE 'Technology' = ANY(categories);
```

## 🛠️ Local Development

To run the script locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="https://pmijctxikafxsqdqxdej.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-key"

# Run the script
python update_podcasts.py
```

## 📝 Adding New Podcasts

Simply edit `feeds.json` and commit the changes. The next workflow run will automatically process the new feeds.

## 🚨 Error Handling

- Invalid RSS feeds are skipped with error logging
- Failed episodes don't stop podcast processing
- Workflow artifacts capture logs on failure
- Duplicate detection prevents data duplication

## 📈 Scaling Considerations

Current limits (free tier friendly):
- ~100 podcasts maximum
- ~5,000 episodes total
- 50 recent episodes per podcast
- Daily update frequency

To scale beyond this:
- Increase Supabase plan
- Optimize episode limits
- Add incremental updates
- Implement feed validation

## 🔒 Security Notes

- Service role key stored as GitHub secret
- No sensitive data in repository
- Read-only RSS feed access
- Supabase RLS can be enabled for additional security

## 📱 Mobile App Integration

Your mobile app should:
- Use Supabase client SDKs or REST API
- Implement full-text search on titles/descriptions
- Filter by categories, language, or date ranges
- Display podcast and episode metadata
- Link to audio URLs for playback

## 🤝 Contributing

1. Add new RSS feeds to `feeds.json`
2. Test changes with manual workflow triggers
3. Submit pull requests for script improvements
4. Report issues with specific RSS feeds

## 📄 License

This project is open source and available under the MIT License.