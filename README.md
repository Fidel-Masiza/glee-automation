# glee-automation
# Shift Auto-Claimer - Render Deployment

## Features
- 🚀 Auto-claims available shifts
- 📊 Tracks seen shifts for faster scanning
- 🌐 Runs 24/7 on Render
- ⏰ Auto-stops after 12 hours (Render free tier limit)
- 📈 Shows real-time statistics

## Deploy to Render

### Method 1: One-Click Deploy
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/shift-claimer)

### Method 2: Manual Deployment
1. **Push code to GitHub** (this repository)
2. **Go to [render.com](https://render.com)**
3. **Click "New +" → "Blueprint"**
4. **Connect your GitHub repository**
5. **Render will detect `render.yaml` and deploy automatically**

## Local Development
```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run locally
python render_shift_claimer.py
