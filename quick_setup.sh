#!/bin/bash

# Quick Setup Script for Podcast Metadata System
# This script helps automate the GitHub repository setup

echo "🎙️ Podcast Metadata System - Quick Setup"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "feeds.json" ]; then
    echo "❌ Error: Please run this script from the project directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📋 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial podcast metadata system setup

🎙️ Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
    git branch -M main
else
    echo "✅ Git repository already initialized"
fi

echo ""
echo "📝 Next steps:"
echo "1. Create a GitHub repository at: https://github.com/new"
echo "2. Run these commands to push your code:"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
echo "   git push -u origin main"
echo ""
echo "3. Set up GitHub Secrets in Settings > Secrets and variables > Actions:"
echo "   - SUPABASE_URL: https://pmijctxikafxsqdqxdej.supabase.co"
echo "   - SUPABASE_SERVICE_ROLE_KEY: [Your service role key from Supabase]"
echo ""
echo "4. Run the SQL schema in your Supabase project:"
echo "   - Copy contents of supabase_schema.sql"
echo "   - Paste in Supabase SQL Editor and run"
echo ""
echo "📖 See SETUP_GUIDE.md for detailed instructions"