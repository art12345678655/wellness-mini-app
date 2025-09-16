# 🍎 Nutrition Mini App

A Telegram Mini App that displays nutrition progress rings with real user data from Supabase.

## 🚀 Features

- 📊 **Real-time nutrition tracking** - Fetches data from your Supabase database
- 🍎 **Apple Fitness-style rings** - Beautiful canvas-based progress visualization
- 📱 **Mobile optimized** - Works perfectly on Telegram mobile apps
- 🔄 **Auto-refresh** - Updates every 30 seconds
- 🤖 **Telegram WebApp integration** - Seamless in-app experience
- 🎯 **Personalized data** - Shows each user's individual nutrition goals and progress

## 🛠️ Setup Instructions

### 1. Environment Variables

Create a `.env` file with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
MINI_APP_URL=https://your-mini-app.onrender.com
```

**Note:** If Supabase credentials are not provided, the app will use demo data but still allow real user data updates via API.

### 2. Real User Data Integration

To show each user's actual nutrition data instead of demo data:

#### Option A: Update via API (Recommended)

```python
import requests

def update_user_mini_app(user_id, targets, consumed_today, meal_count):
    """Update user's nutrition data in the mini app"""
    url = "https://your-mini-app.onrender.com/api/update-user-data"
    data = {
        "user_id": str(user_id),
        "targets": {
            "calories": targets.get('calories', 2000),
            "protein_g": targets.get('protein_g', 150),
            "fats_g": targets.get('fats_g', 65),
            "carbs_g": targets.get('carbs_g', 250)
        },
        "consumed_today": {
            "calories": consumed_today.get('calories', 0),
            "protein_g": consumed_today.get('protein_g', 0),
            "fats_g": consumed_today.get('fats_g', 0),
            "carbs_g": consumed_today.get('carbs_g', 0)
        },
        "meal_count": meal_count
    }

    response = requests.post(url, json=data)
    return response.json()

# Usage in your bot:
update_user_mini_app(
    user_id=message.from_user.id,
    targets=user_nutrition_targets,
    consumed_today=user_daily_consumption,
    meal_count=user_meal_count
)
```

#### Option B: Direct Function Call

If your bot runs on the same server, you can import the utility function:

```python
from web_server import update_user_nutrition_data

# Update user data
update_user_nutrition_data(
    user_id="123456789",
    targets={'calories': 2000, 'protein_g': 150, 'fats_g': 65, 'carbs_g': 250},
    consumed_today={'calories': 450, 'protein_g': 35, 'fats_g': 15, 'carbs_g': 60},
    meal_count=2
)
```

### 3. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python mini_app_server.py
```

Visit: `http://localhost:8080/nutrition-dashboard?user_id=YOUR_TELEGRAM_ID`

### 3. Deploy to Render

1. **Create new Render Web Service**
2. **Connect your GitHub repository**
3. **Set build settings:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python mini_app_server.py`
4. **Add environment variables:**
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   PORT=10000
   ```
5. **Deploy!** 🚀

### 4. Update Your Bot

In your main bot repository, update the dashboard command to point to your mini app:

```python
# In tg_bot.py, update the dashboard command
keyboard = [
    [InlineKeyboardButton("📊 Открыть Dashboard",
     web_app=WebAppInfo(url=f"{MINI_APP_URL}/nutrition-dashboard?user_id={user_id}"))]
]
```

Add to your bot's environment variables:
```
MINI_APP_URL=https://your-mini-app.onrender.com
```

## 📁 Project Structure

```
wellness-mini-app/
├── mini_app_server.py      # Main web server with real user data support
├── config.py               # Configuration and environment variables
├── supabase_db.py          # Supabase database client
├── nutrition_rings.html    # Frontend dashboard
├── nutritions_files.html   # Alternative dashboard layout
├── web_server.py          # Alternative aiohttp server implementation
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🔄 Real User Data Integration

The mini app now supports real user data through API endpoints:

### For Bot Developers

To update user nutrition data, your bot can send POST requests:

```python
import requests

def update_user_nutrition(user_id, targets, consumed_today, meal_count=0):
    """Update user's nutrition data in the mini app"""
    url = "https://your-mini-app.onrender.com/api/update-user-data"
    data = {
        "user_id": str(user_id),
        "targets": {
            "calories": targets.get('calories', 2000),
            "protein_g": targets.get('protein_g', 150),
            "fats_g": targets.get('fats_g', 65),
            "carbs_g": targets.get('carbs_g', 250)
        },
        "consumed_today": {
            "calories": consumed_today.get('calories', 0),
            "protein_g": consumed_today.get('protein_g', 0),
            "fats_g": consumed_today.get('fats_g', 0),
            "carbs_g": consumed_today.get('carbs_g', 0)
        },
        "meal_count": meal_count
    }

    response = requests.post(url, json=data)
    return response.json()

# Example usage in your bot:
update_user_nutrition(
    user_id=532684618,  # Telegram user ID
    targets={'calories': 2500, 'protein_g': 200, 'fats_g': 80, 'carbs_g': 300},
    consumed_today={'calories': 301, 'protein_g': 39, 'fats_g': 19, 'carbs_g': 49},
    meal_count=1
)
```

### API Endpoints

- `GET /nutrition-dashboard?user_id={telegram_id}` - Get user's nutrition dashboard
- `POST /api/update-user-data` - Update user's nutrition data
- `GET /health` - Health check endpoint

## 🔌 API Endpoints

- `GET /` - Main dashboard (redirects to nutrition-dashboard)
- `GET /nutrition-dashboard?user_id={telegram_id}` - Nutrition dashboard for user
- `GET /health` - Health check for Render
- `GET /api/user/{user_id}` - JSON API for user nutrition data

## 🎯 How It Works

1. **User sends `/dashboard`** in Telegram
2. **Bot responds** with inline keyboard containing WebApp button
3. **User clicks button** → Opens mini app with their nutrition data
4. **Mini app fetches** real data from Supabase based on Telegram user ID
5. **Beautiful rings** display progress towards daily nutrition goals
6. **Auto-refresh** every 30 seconds to show latest data

## 📊 Data Flow

```
Telegram Bot → Mini App URL → Supabase Query → User Data → HTML Injection → Beautiful Rings
```

## 🔒 Security

- ✅ **User ID validation** - Only shows user's own data
- ✅ **HTTPS required** - Telegram WebApps require secure connections
- ✅ **Supabase authentication** - Uses your existing auth setup
- ✅ **Environment variables** - No sensitive data in code

## 🐛 Troubleshooting

### Mini App Not Loading
- Check your `MINI_APP_URL` environment variable
- Ensure HTTPS is enabled (required for Telegram WebApps)
- Verify Supabase credentials are correct

### Data Not Showing
- Check user has nutrition targets set in Supabase
- Verify `user_id` matches Telegram user ID
- Check Supabase logs for query errors

### Rings Not Animating
- Ensure JavaScript is enabled in browser
- Check browser console for errors
- Verify HTML template is loading correctly

## 🚀 Production Deployment

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render:**
   - Create new Web Service
   - Connect GitHub repository
   - Set environment variables
   - Deploy!

3. **Update Bot:**
   - Add `MINI_APP_URL` environment variable
   - Update dashboard command URL
   - Redeploy bot

## 📈 Monitoring

- **Health Check:** Visit `/health` endpoint
- **Logs:** Check Render service logs
- **Supabase:** Monitor database queries
- **Telegram:** Test `/dashboard` command

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**🎉 Ready to deploy your nutrition mini app!**

Your users will love seeing their nutrition progress in beautiful, interactive rings! 🍎📊
