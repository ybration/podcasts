# podcasts
```markdown
# 📡 Podcast Feed Aggregator (GitHub-Powered Backend)

This repo is a lightweight podcast backend built entirely on **GitHub** using:

- ✅ A manually curated list of podcast RSS feeds (`feeds.json`)
- ✅ A GitHub Action that fetches, parses, and updates feed data on a schedule
- ✅ Output data (`rss_output.json`) that apps can consume directly — no server required

---

## 🧱 Project Structure

```

/
├── feeds.json           # List of all podcast RSS URLs
├── rss\_output.json      # Parsed and updated feed + episode metadata
├── fetch\_feeds.py       # Python script that does the fetching/parsing
└── .github/
└── workflows/
└── fetch-rss.yml   # GitHub Action that runs the fetch script every hour

```

---

## 🚀 How It Works

1. You manually add RSS feed URLs to `feeds.json`.
2. A GitHub Action runs automatically every hour (or on demand).
3. It fetches metadata from each feed:
   - Podcast title, link, RSS URL
   - First 5 episodes: title, description, publish date, etc.
4. The script saves this to `rss_output.json`.
5. Your app fetches the latest `rss_output.json` to show current podcast content.

---

## ➕ Adding New Podcasts

1. Open `feeds.json`
2. Add a new RSS URL (ensure it’s valid JSON)
3. Commit the change
4. The GitHub Action will include the new feed automatically in the next run

---

## 📱 How Apps Use This

- Your app fetches `rss_output.json` from GitHub:
```

[https://raw.githubusercontent.com/YOUR\_USERNAME/YOUR\_REPO/main/rss\_output.json](https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/rss_output.json)

```
- Cache it locally, refresh every X hours, or use pull-to-refresh
- (Optional) You can split feeds by topic or episode files later

---

## 🔐 Private Repo Access (Optional)

If this repo is private and your app needs access:

- Use the GitHub API with a personal access token (PAT)
- Or create a proxy server that reads from this repo and exposes only public data
- Or mirror the output to a public repo using another GitHub Action

---

## 🛠️ To-Do / Ideas

- [ ] Group feeds by category (tech, news, etc.)
- [ ] Add per-feed output files
- [ ] Add tag support
- [ ] Push data to Supabase, S3, or Firebase

---

## 📄 License

MIT — use freely, but respect podcast publishers and never store or redistribute audio directly.

```

---

Would you like me to include:

* Setup instructions for the GitHub Action?
* A link to the GitHub Pages or raw URL if you plan to expose it publicly?

Let me know if you'd like this in your actual repo too.

