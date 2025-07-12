# ✅ Setup Checklist

## What I've Done For You:

✅ **Created complete project structure**
- feeds.json with 5 sample podcasts
- Python script for RSS parsing and Supabase integration
- GitHub Actions workflow for automation
- Database schema for Supabase
- Comprehensive documentation

✅ **Tested the system**
- RSS parsing works correctly
- Dependencies are installed
- Git repository is initialized and committed

✅ **Created your Supabase configuration**
- Project URL: `https://pmijctxikafxsqdqxdej.supabase.co`
- Schema ready to deploy

## What You Need To Do:

### 🗄️ 1. Set Up Supabase Database (5 minutes)
- [ ] Go to: https://supabase.com/dashboard/project/pmijctxikafxsqdqxdej
- [ ] Click "SQL Editor" → "New query"
- [ ] Copy all contents of `supabase_schema.sql`
- [ ] Paste and click "Run"
- [ ] Verify tables appear in "Table Editor"

### 🔑 2. Get Your API Key (2 minutes)
- [ ] In Supabase: Settings → API
- [ ] Copy the "service_role" key (NOT anon key)
- [ ] Save this key for GitHub setup

### 🐙 3. Create GitHub Repository (5 minutes)
- [ ] Go to: https://github.com/new
- [ ] Repository name: `podcast-metadata-system`
- [ ] Make it public or private
- [ ] Don't initialize with README
- [ ] Click "Create repository"

### 📤 4. Push Code to GitHub (2 minutes)
```bash
# Replace YOUR_USERNAME and YOUR_REPO_NAME with your actual values
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 🔐 5. Set Up GitHub Secrets (3 minutes)
- [ ] In your GitHub repo: Settings → Secrets and variables → Actions
- [ ] Click "New repository secret"
- [ ] Add secret: `SUPABASE_URL` = `https://pmijctxikafxsqdqxdej.supabase.co`
- [ ] Add secret: `SUPABASE_SERVICE_ROLE_KEY` = [your service role key]

### 🧪 6. Test Everything (5 minutes)
- [ ] GitHub repo: Actions → "Update Podcast Metadata" → "Run workflow"
- [ ] Wait for green checkmark
- [ ] Check Supabase tables for data

## 🎯 Expected Results:

After completing the setup:
- **podcasts table**: 5 entries (Planet Money, Serial, The Daily, etc.)
- **episodes table**: 100+ episode entries
- **Automatic updates**: Daily at 6:00 AM UTC
- **Ready for mobile app**: Direct Supabase connection

## 📱 For Your Mobile App:

**Supabase Connection:**
- URL: `https://pmijctxikafxsqdqxdej.supabase.co`
- Anon Key: Get from Supabase Settings → API (different from service role)

**Example Queries:**
```sql
-- Search podcasts
SELECT * FROM podcasts WHERE title ILIKE '%news%';

-- Recent episodes  
SELECT e.title, p.title as podcast_name, e.published_at
FROM episodes e 
JOIN podcasts p ON e.podcast_id = p.id 
ORDER BY e.published_at DESC LIMIT 10;
```

---

**Total setup time: ~20 minutes**
**System status after setup: Fully automated** 🚀