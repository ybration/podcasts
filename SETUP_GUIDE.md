# 🚀 Complete Setup Guide

Follow these steps exactly to get your podcast metadata system running.

## ✅ Step 1: Set Up Supabase Database

1. **Go to your Supabase project**: https://supabase.com/dashboard/project/pmijctxikafxsqdqxdej

2. **Create the database schema**:
   - Click on "SQL Editor" in the left sidebar
   - Click "New query"
   - Copy the entire contents of `supabase_schema.sql` from this project
   - Paste it into the SQL editor
   - Click "Run" (bottom right)
   - You should see "Success. No rows returned" - this is correct!

3. **Get your API key**:
   - Click "Settings" in the left sidebar
   - Click "API" 
   - Copy the "service_role" key (NOT the anon key)
   - Save this key - you'll need it for GitHub

4. **Verify tables were created**:
   - Click "Table Editor" in the left sidebar
   - You should see two tables: `podcasts` and `episodes`

## ✅ Step 2: Set Up GitHub Repository

1. **Create a new GitHub repository**:
   - Go to https://github.com/new
   - Name it something like "podcast-metadata-system"
   - Make it public or private (your choice)
   - Don't initialize with README (we have our own files)

2. **Upload your project files**:
   ```bash
   cd /Users/masa/Desktop/Podcast_RSS
   git init
   git add .
   git commit -m "Initial podcast metadata system setup"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

3. **Set up GitHub Secrets**:
   - Go to your GitHub repository
   - Click "Settings" tab
   - Click "Secrets and variables" > "Actions"
   - Click "New repository secret"
   - Add these two secrets:

   **Secret 1:**
   - Name: `SUPABASE_URL`
   - Value: `https://pmijctxikafxsqdqxdej.supabase.co`

   **Secret 2:**
   - Name: `SUPABASE_SERVICE_ROLE_KEY`
   - Value: [Paste your service role key from Supabase]

## ✅ Step 3: Test the System

1. **Manual test run**:
   - In your GitHub repository, click "Actions" tab
   - Click "Update Podcast Metadata" workflow
   - Click "Run workflow" button
   - Click the green "Run workflow" button
   - Wait for it to complete (should take 1-2 minutes)

2. **Check results in Supabase**:
   - Go back to your Supabase Table Editor
   - Click on the `podcasts` table
   - You should see 5 podcast entries
   - Click on the `episodes` table  
   - You should see many episode entries

## ✅ Step 4: Verify Everything Works

1. **Check podcast data**:
   - In Supabase Table Editor, view the `podcasts` table
   - You should see entries for Planet Money, Serial, The Daily, etc.

2. **Check episode data**:
   - View the `episodes` table
   - Each podcast should have multiple episodes

3. **Test queries** (optional):
   - Go to SQL Editor in Supabase
   - Try this query to search podcasts:
   ```sql
   SELECT title, description, categories 
   FROM podcasts 
   WHERE 'Technology' = ANY(categories);
   ```

## 🎯 What Happens Next

- **Automatic updates**: The system will run daily at 6:00 AM UTC
- **Adding podcasts**: Edit `feeds.json` and commit to trigger updates
- **Mobile app**: Connect directly to your Supabase database

## 🆘 Troubleshooting

**If the GitHub Action fails:**
1. Check the Actions tab for error logs
2. Verify your Supabase secrets are correct
3. Make sure the database schema was created properly

**If no data appears in Supabase:**
1. Check that the service role key has the right permissions
2. Verify the RSS feeds in `feeds.json` are valid
3. Look at the GitHub Actions logs for specific errors

**Common issues:**
- Wrong API key: Use service_role, not anon key
- Schema not created: Re-run the SQL from `supabase_schema.sql`
- Network issues: RSS feeds might be temporarily unavailable

## 📱 Next Steps for Mobile App

Your mobile app can now connect to Supabase using:
- **URL**: `https://pmijctxikafxsqdqxdej.supabase.co`
- **Anon Key**: Get from Supabase Settings > API (different from service role key)

Example queries for your app:
```sql
-- Search podcasts
SELECT * FROM podcasts WHERE title ILIKE '%technology%';

-- Get recent episodes
SELECT e.*, p.title as podcast_title 
FROM episodes e 
JOIN podcasts p ON e.podcast_id = p.id 
ORDER BY e.published_at DESC 
LIMIT 20;

-- Filter by category
SELECT * FROM podcasts WHERE 'News' = ANY(categories);
```

---

🎉 **You're all set!** Your podcast metadata system is now running automatically!