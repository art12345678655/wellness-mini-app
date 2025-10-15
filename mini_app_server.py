#!/usr/bin/env python3
"""
Simple Mini App Server for Nutrition Dashboard
Uses only standard library - no external dependencies
"""

import os
import json
import logging
import asyncio
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time
from supabase_db import SupabaseMiniApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for user nutrition data
# In production, this should be replaced with a proper database
USER_DATA = {}

# Sample user data for testing
sample_data = {
    'user_123': {
        'user_id': 'user_123',
        'targets': {'calories': 2500, 'protein_g': 200, 'fats_g': 80, 'carbs_g': 300},
        'consumed_today': {'calories': 301, 'protein_g': 39, 'fats_g': 19, 'carbs_g': 49},
        'remaining': {'calories': 2199, 'protein_g': 161, 'fats_g': 61, 'carbs_g': 251},
        'progress': {'calories': 0.12, 'protein_g': 0.195, 'fats_g': 0.2375, 'carbs_g': 0.1633},
        'meal_count': 1
    }
}

# Initialize with sample data
USER_DATA.update(sample_data)

def update_user_nutrition_data(user_id, targets=None, consumed_today=None, meal_count=0):
    """
    Utility function for bots to update user nutrition data.
    """
    user_id_str = str(user_id)

    # Calculate remaining amounts
    remaining = {}
    progress = {}

    if targets and consumed_today:
        remaining = {
            'calories': max(0, targets.get('calories', 2000) - consumed_today.get('calories', 0)),
            'protein_g': max(0, targets.get('protein_g', 150) - consumed_today.get('protein_g', 0)),
            'fats_g': max(0, targets.get('fats_g', 65) - consumed_today.get('fats_g', 0)),
            'carbs_g': max(0, targets.get('carbs_g', 250) - consumed_today.get('carbs_g', 0))
        }

        progress = {
            'calories': min(1.0, consumed_today.get('calories', 0) / targets.get('calories', 2000)),
            'protein_g': min(1.0, consumed_today.get('protein_g', 0) / targets.get('protein_g', 150)),
            'fats_g': min(1.0, consumed_today.get('fats_g', 0) / targets.get('fats_g', 65)),
            'carbs_g': min(1.0, consumed_today.get('carbs_g', 0) / targets.get('carbs_g', 250))
        }

    USER_DATA[user_id_str] = {
        'user_id': user_id_str,
        'targets': targets or {'calories': 2000, 'protein_g': 150, 'fats_g': 65, 'carbs_g': 250},
        'consumed_today': consumed_today or {'calories': 0, 'protein_g': 0, 'fats_g': 0, 'carbs_g': 0},
        'remaining': remaining or {'calories': 2000, 'protein_g': 150, 'fats_g': 65, 'carbs_g': 250},
        'progress': progress or {'calories': 0, 'protein_g': 0, 'fats_g': 0, 'carbs_g': 0},
        'meal_count': meal_count
    }

    logger.info(f"Updated nutrition data for user {user_id}: {USER_DATA[user_id_str]}")
    return USER_DATA[user_id_str]

class NutritionDataHandler:
    """Handler for getting real nutrition data from Supabase - SAME LOGIC AS /consumed and /left commands"""
    
    def __init__(self):
        self.supabase_client = SupabaseMiniApp()
    
    async def get_user_nutrition_data(self, user_id: str) -> dict:
        """Get REAL nutrition data using SAME logic as /consumed and /left commands"""
        logger.info(f"Getting REAL nutrition data for user {user_id} - SAME LOGIC AS BOT COMMANDS")
        
        try:
            # Convert string user_id to int for database query
            user_telegram_id = int(user_id)
            
            # STEP 1: Get user's daily nutrition targets (SAME AS /consumed command)
            user_profile = await self.supabase_client.get_user_profile(user_telegram_id)
            logger.info(f"User profile from database: {user_profile}")
            
            if not user_profile:
                logger.error(f"No user profile found for {user_telegram_id}")
                raise Exception(f"No user profile found for user {user_telegram_id}")
            
            # Get daily targets and convert Decimal to float (SAME AS /consumed command)
            daily_calories = float(user_profile.get('calorie_target', 0))
            daily_protein = float(user_profile.get('protein_target_g', 0))
            daily_carbs = float(user_profile.get('carbs_target_g', 0))
            daily_fats = float(user_profile.get('fat_target_g', 0))
            
            logger.info(f"REAL Daily targets - Calories: {daily_calories}, Protein: {daily_protein}, Carbs: {daily_carbs}, Fats: {daily_fats}")
            
            if not all([daily_calories, daily_protein, daily_carbs, daily_fats]):
                logger.error(f"Missing nutrition targets for user {user_telegram_id}")
                raise Exception(f"Missing nutrition targets for user {user_telegram_id}")
            
            # STEP 2: Get today's total nutrition from all logged meals (SAME AS /consumed command)
            today_nutrition = await self.supabase_client.get_today_nutrition_summary(user_telegram_id)
            logger.info(f"REAL Today's nutrition summary: {today_nutrition}")
            
            # Get today's totals from database (SAME AS /consumed command)
            today_calories = today_nutrition.get('total_calories', 0)
            today_protein = today_nutrition.get('total_protein_g', 0)
            today_carbs = today_nutrition.get('total_carbs_g', 0)
            today_fats = today_nutrition.get('total_fat_g', 0)
            
            logger.info(f"REAL Today's consumed - Calories: {today_calories}, Protein: {today_protein}g, Carbs: {today_carbs}g, Fats: {today_fats}g")
            
            # STEP 3: Calculate remaining amounts (SAME AS /left command)
            calories_remaining = max(0, daily_calories - today_calories)
            protein_remaining = max(0, daily_protein - today_protein)
            carbs_remaining = max(0, daily_carbs - today_carbs)
            fats_remaining = max(0, daily_fats - today_fats)
            
            logger.info(f"REAL Calculated remaining - Calories: {calories_remaining}, Protein: {protein_remaining}g, Carbs: {carbs_remaining}g, Fats: {fats_remaining}g")
            
            return {
                'calories': {'value': calories_remaining, 'total': daily_calories},
                'protein': {'value': protein_remaining, 'total': daily_protein},
                'carbs': {'value': carbs_remaining, 'total': daily_carbs},
                'fats': {'value': fats_remaining, 'total': daily_fats}
            }
            
        except Exception as e:
            logger.error(f"Error getting REAL data for user {user_id}: {e}")
            raise Exception(f"Failed to get real nutrition data for user {user_id}: {str(e)}")

# Global supabase client instance for historical data
supabase_client = SupabaseMiniApp()

async def get_historical_nutrition_data(user_id: str, days: int = 7) -> dict:
    """Get historical nutrition data for the last N days"""
    try:
        logger.info(f"🔍 DEBUG: get_historical_nutrition_data called with user_id='{user_id}' (type: {type(user_id)}), days={days}")

        user_telegram_id = int(user_id)
        logger.info(f"🔍 DEBUG: Converted user_id to user_telegram_id={user_telegram_id} (type: {type(user_telegram_id)})")
        logger.info(f"🍎 Getting {days} days of REAL historical nutrition data for user {user_telegram_id}")

        # Get user profile for targets (same for all days)
        user_profile = await supabase_client.get_user_profile(user_telegram_id)

        if not user_profile:
            logger.error(f"No user profile found for user {user_telegram_id}")
            raise Exception(f"User profile not found")

        # Get targets
        daily_calories = float(user_profile.get('calorie_target', 2000))
        daily_protein = float(user_profile.get('protein_target_g', 150))
        daily_carbs = float(user_profile.get('carbs_target_g', 250))
        daily_fats = float(user_profile.get('fat_target_g', 65))

        # Get REAL nutrition data directly from recent_daily_nutrition_summary view
        logger.info(f"🔍 DEBUG: Using recent_daily_nutrition_summary view for user_telegram_id={user_telegram_id}")

        recent_summaries = await supabase_client.get_recent_daily_summaries(user_telegram_id, days)
        logger.info(f"🔍 DEBUG: Got {len(recent_summaries)} days from recent_daily_nutrition_summary view")

        # Convert view data to historical format, ensuring we have exactly 7 days
        today = datetime.datetime.now(datetime.timezone.utc).date()
        historical_data = []
        total_real_calories = 0
        days_with_data = 0

        # Create a lookup dict from the view data
        summary_lookup = {summary['date']: summary for summary in recent_summaries}

        for i in range(days):
            target_date = today - datetime.timedelta(days=days - 1 - i)
            date_str = target_date.isoformat()

            if date_str in summary_lookup:
                # Use data from recent_daily_nutrition_summary view
                summary = summary_lookup[date_str]
                calories_consumed = summary['total_calories']
                protein_consumed = summary['total_protein_g']
                carbs_consumed = summary['total_carbs_g']
                fats_consumed = summary['total_fat_g']

                logger.info(f"✅ {date_str}: Found in view - {calories_consumed} calories, {summary['meals_logged_count']} meals")
            else:
                # No data for this day
                calories_consumed = 0
                protein_consumed = 0
                carbs_consumed = 0
                fats_consumed = 0

                logger.info(f"❌ {date_str}: No data found in recent_daily_nutrition_summary view")

            # Track real data statistics
            if calories_consumed > 0:
                days_with_data += 1
            total_real_calories += calories_consumed

            historical_data.append({
                'date': date_str,
                'calories': calories_consumed,
                'protein': protein_consumed,
                'carbs': carbs_consumed,
                'fats': fats_consumed
            })

            logger.info(f"🔍 DEBUG: Day {i+1} ({date_str}): calories={calories_consumed}, protein={protein_consumed}, carbs={carbs_consumed}, fats={fats_consumed}")

        # Always return real data from database (no sample data substitution)
        average_calories = total_real_calories / days if days > 0 else 0
        logger.info(f"✅ REAL DATA ONLY: {days_with_data}/{days} days with data, {total_real_calories} total calories, {average_calories:.0f} avg/day")

        logger.info(f"✅ Successfully retrieved {days} days of historical data")
        return {
            'daily_targets': {
                'calories': daily_calories,
                'protein': daily_protein,
                'carbs': daily_carbs,
                'fats': daily_fats
            },
            'historical_data': historical_data
        }

    except Exception as e:
        logger.error(f"❌ Error getting historical data for user {user_id}: {e}")
        raise Exception(f"Failed to get historical nutrition data for user {user_id}: {str(e)}")

async def get_user_streak_data(user_id: str) -> dict:
    """Get user's current streak and days since last meal log from the database"""
    try:
        logger.info(f"🔥 Getting streak data for user {user_id}")
        user_telegram_id = int(user_id)

        # Get current_streak, days_since_last_meal_log, and coins from the database
        result = supabase_client.client.table('users').select('current_streak, days_since_last_meal_log, coins').eq('user_id', user_telegram_id).execute()

        if not result.data:
            logger.warning(f"No user found for user {user_telegram_id}, returning default values")
            return {'current_streak': 0, 'days_since_last_meal_log': 0, 'coins': 0}

        current_streak = result.data[0].get('current_streak', 0) or 0
        days_since_last_meal_log = result.data[0].get('days_since_last_meal_log', 0) or 0
        coins = result.data[0].get('coins', 0) or 0
        logger.info(f"✅ User {user_telegram_id} - current_streak: {current_streak}, days_since_last_meal_log: {days_since_last_meal_log}, coins: {coins}")

        return {
            'current_streak': current_streak,
            'days_since_last_meal_log': days_since_last_meal_log,
            'coins': coins
        }

    except Exception as e:
        logger.error(f"❌ Error getting streak data for user {user_id}: {e}")
        return {'current_streak': 0, 'days_since_last_meal_log': 0, 'coins': 0}

class RequestHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        """Handle HEAD requests (for health checks)"""
        self.do_GET()

    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        logger.info(f"📡 Request: {path}")

        try:
            if path == '/' or path == '/nutrition-dashboard':
                self.handle_nutrition_dashboard(query_params)
            elif path == '/test':
                self.handle_test_dashboard()
            elif path == '/health':
                self.handle_health_check()
            elif path == '/api/nutrition-data':
                self.handle_api_nutrition_data(query_params)
            elif path == '/api/historical-data':
                self.handle_api_historical_data(query_params)
            elif path == '/api/streak-data':
                self.handle_api_streak_data(query_params)
            elif path.startswith('/images/'):
                self.handle_static_file(path)
            else:
                self.send_error(404, "Not Found")

        except Exception as e:
            logger.error(f"❌ Error handling request: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        logger.info(f"📡 POST Request: {path}")

        try:
            if path == '/api/update-user-data':
                self.handle_update_user_data()
            else:
                self.send_error(404, "Not Found")

        except Exception as e:
            logger.error(f"❌ Error handling POST request: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def handle_update_user_data(self):
        """Handle user data update requests"""
        try:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            user_id = str(data.get('user_id', 'user_123'))

            # Update user data
            update_user_nutrition_data(
                user_id=user_id,
                targets=data.get('targets'),
                consumed_today=data.get('consumed_today'),
                meal_count=data.get('meal_count', 0)
            )

            # Send success response
            response = {
                'status': 'success',
                'message': f'Updated data for user {user_id}'
            }

            self.send_json_response(response)

        except Exception as e:
            logger.error(f"❌ Error updating user data: {e}")
            self.send_json_response({
                'status': 'error',
                'message': str(e)
            }, status_code=400)

    def handle_nutrition_dashboard(self, query_params):
        """Serve the nutrition dashboard"""
        user_id = query_params.get('user_id', [None])[0]

        if not user_id:
            self.send_error(400, "User ID required")
            return

        try:
            logger.info(f"📱 Mini app accessed by user {user_id}")

            # Get user data from REAL database
            nutrition_handler = NutritionDataHandler()
            
            # Run async database query
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                user_data = loop.run_until_complete(nutrition_handler.get_user_nutrition_data(user_id))
            finally:
                loop.close()

            # Read HTML template
            html_content = self.read_html_file()
            if not html_content:
                self.send_error(500, "HTML template not found")
                return

            # Inject data
            html_content = self.inject_user_data(html_content, user_data)
            self.send_html_response(html_content)

        except Exception as e:
            logger.error(f"❌ Error serving dashboard: {e}")
            self.send_error(500, f"Error loading dashboard: {str(e)}")

    def handle_test_dashboard(self):
        """Serve test dashboard without user data"""
        try:
            html_content = self.read_html_file()
            if not html_content:
                self.send_error(500, "HTML template not found")
                return

            # Add basic Telegram WebApp integration
            telegram_script = '''
            <script src="https://telegram.org/js/telegram-web-app.js"></script>
            <script>
                console.log('Test Mini app loaded');
                const tg = window.Telegram.WebApp;
                tg.expand();
                tg.ready();
                console.log('Telegram WebApp test ready');
                if (tg.MainButton) {
                    tg.MainButton.setText('Test Dashboard');
                }
            </script>
            '''

            html_content = html_content.replace('</head>', f'{telegram_script}</head>')
            self.send_html_response(html_content)

        except Exception as e:
            logger.error(f"❌ Error serving test dashboard: {e}")
            self.send_error(500, f"Test dashboard error: {str(e)}")

    def handle_health_check(self):
        """Health check endpoint"""
        response = {
            "status": "healthy",
            "service": "nutrition-mini-app",
            "database": "mock",
            "timestamp": str(time.time())
        }
        self.send_json_response(response)

    def handle_api_nutrition_data(self, query_params):
        """API endpoint to return JSON nutrition data for a user"""
        try:
            # Get user_id from query parameters
            user_id = query_params.get('user_id', ['user_123'])[0]
            logger.info(f"🍎 API request for user: {user_id}")

            # Get real nutrition data using Supabase
            real_data = asyncio.run(self.get_real_user_nutrition_data(user_id))

            # Calculate consumed amounts (opposite of remaining)
            calories_consumed = real_data['calories']['total'] - real_data['calories']['value']
            protein_consumed = real_data['protein']['total'] - real_data['protein']['value']
            carbs_consumed = real_data['carbs']['total'] - real_data['carbs']['value']
            fat_consumed = real_data['fats']['total'] - real_data['fats']['value']

            # Format response to match expected structure
            response = {
                "user_id": user_id,
                "targets": {
                    "calories": real_data['calories']['total'],
                    "protein_g": real_data['protein']['total'],
                    "carbs_g": real_data['carbs']['total'],
                    "fats_g": real_data['fats']['total']
                },
                "consumed_today": {
                    "calories": calories_consumed,
                    "protein_g": protein_consumed,
                    "carbs_g": carbs_consumed,
                    "fats_g": fat_consumed
                },
                "remaining": {
                    "calories": real_data['calories']['value'],
                    "protein_g": real_data['protein']['value'],
                    "carbs_g": real_data['carbs']['value'],
                    "fats_g": real_data['fats']['value']
                }
            }

            logger.info(f"📊 API response: Consumed {calories_consumed} calories, {protein_consumed}g protein")
            self.send_json_response(response)

        except Exception as e:
            logger.error(f"❌ API Error for user {user_id}: {e}")
            # Return fallback data if real data fails
            fallback_response = {
                "user_id": user_id,
                "targets": {"calories": 2500, "protein_g": 200, "carbs_g": 300, "fats_g": 80},
                "consumed_today": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fats_g": 0},
                "remaining": {"calories": 2500, "protein_g": 200, "carbs_g": 300, "fats_g": 80}
            }
            self.send_json_response(fallback_response)

    def handle_api_historical_data(self, query_params):
        """API endpoint to return historical nutrition data for analytics"""
        try:
            # Get user_id and days from query parameters
            user_id = query_params.get('user_id', ['user_123'])[0]
            days = int(query_params.get('days', ['7'])[0])
            logger.info(f"🔍 DEBUG: Historical API request - Raw user_id: {user_id}, days: {days}")

            # DEBUG: Log the exact user ID we're using
            logger.info(f"🔍 DEBUG: About to call get_historical_nutrition_data with user_id={user_id}")

            # Get historical nutrition data
            historical_data = asyncio.run(get_historical_nutrition_data(user_id, days))

            # DEBUG: Log what we got back from the database
            logger.info(f"🔍 DEBUG: Raw historical_data from database: {historical_data}")

            # Format response for frontend
            response = {
                "user_id": user_id,
                "days": days,
                "daily_targets": historical_data['daily_targets'],
                "last_7_days": []
            }

            # Convert historical data to expected format
            for i, day_data in enumerate(historical_data['historical_data']):
                day_response = {
                    "date": day_data['date'],
                    "calories": day_data['calories'],
                    "protein": day_data['protein'],
                    "carbs": day_data['carbs'],
                    "fats": day_data['fats'],
                    "caloriesSpent": 0  # Set to 0 as requested
                }
                response["last_7_days"].append(day_response)

                # DEBUG: Log each day's data
                logger.info(f"🔍 DEBUG: Day {i+1} ({day_data['date']}): calories={day_data['calories']}, protein={day_data['protein']}, carbs={day_data['carbs']}, fats={day_data['fats']}")

            # DEBUG: Log the final response being sent to frontend
            logger.info(f"🔍 DEBUG: Final API response being sent to frontend:")
            logger.info(f"🔍 DEBUG: - user_id: {response['user_id']}")
            logger.info(f"🔍 DEBUG: - daily_targets: {response['daily_targets']}")
            logger.info(f"🔍 DEBUG: - last_7_days count: {len(response['last_7_days'])}")
            for i, day in enumerate(response['last_7_days']):
                logger.info(f"🔍 DEBUG: - Day {i+1}: {day}")

            logger.info(f"📈 Historical API response: {len(response['last_7_days'])} days of data")
            self.send_json_response(response)

        except Exception as e:
            logger.error(f"❌ Historical API Error for user {user_id}: {e}")
            # Return fallback empty data if real data fails
            fallback_response = {
                "user_id": user_id,
                "days": days,
                "daily_targets": {"calories": 2500, "protein": 200, "carbs": 300, "fats": 80},
                "last_7_days": []
            }
            # Fill with empty days
            today = datetime.datetime.now(datetime.timezone.utc).date()
            for i in range(days):
                target_date = today - datetime.timedelta(days=days - 1 - i)
                fallback_response["last_7_days"].append({
                    "date": target_date.isoformat(),
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fats": 0,
                    "caloriesSpent": 0
                })
            self.send_json_response(fallback_response)

    def handle_api_streak_data(self, query_params):
        """API endpoint to return user's current streak and days since last meal log"""
        try:
            # Get user_id from query parameters
            user_id = query_params.get('user_id', ['user_123'])[0]
            logger.info(f"🔥 Streak data API request for user: {user_id}")

            # Get both streak metrics from database
            streak_data = asyncio.run(get_user_streak_data(user_id))
            logger.info(f"📊 Streak data for user {user_id}: {streak_data}")

            # Format response with all three values
            response = {
                "user_id": user_id,
                "current_streak": streak_data.get('current_streak', 0),
                "days_since_last_meal_log": streak_data.get('days_since_last_meal_log', 0),
                "coins": streak_data.get('coins', 0)
            }

            self.send_json_response(response)
        except Exception as e:
            logger.error(f"❌ Streak data API Error for user {user_id}: {e}")
            # Return fallback of 0 if API fails
            fallback_response = {
                "user_id": user_id,
                "current_streak": 0,
                "days_since_last_meal_log": 0,
                "coins": 0
            }
            self.send_json_response(fallback_response)

    def handle_static_file(self, path):
        """Serve static files like images"""
        try:
            # Remove leading slash and construct file path
            file_path = path.lstrip('/')

            # Basic security check
            if '..' in file_path:
                self.send_error(403, "Forbidden")
                return

            # Check if file exists
            if not os.path.exists(file_path):
                self.send_error(404, "File not found")
                return

            # Determine content type
            if file_path.endswith('.png'):
                content_type = 'image/png'
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif file_path.endswith('.gif'):
                content_type = 'image/gif'
            else:
                content_type = 'application/octet-stream'

            # Read and serve file
            with open(file_path, 'rb') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

            logger.info(f"✅ Served static file: {file_path}")

        except Exception as e:
            logger.error(f"❌ Error serving static file {path}: {e}")
            self.send_error(500, f"Error serving file: {str(e)}")

    def read_html_file(self):
        """Read the HTML template file"""
        try:
            with open('nutritions_files.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error("❌ nutritions_files.html not found")
            return None

    def inject_user_data(self, html_content, user_data):
        """Inject user data into HTML template"""
        # Calculate progress based on consumed amounts (consumed / goal)
        # user_data['calories']['value'] is remaining, so consumed = total - remaining
        calories_consumed = user_data['calories']['total'] - user_data['calories']['value']
        protein_consumed = user_data['protein']['total'] - user_data['protein']['value']
        fat_consumed = user_data['fats']['total'] - user_data['fats']['value']
        carbs_consumed = user_data['carbs']['total'] - user_data['carbs']['value']

        calories_progress = calories_consumed / user_data['calories']['total']
        protein_progress = protein_consumed / user_data['protein']['total']
        fat_progress = fat_consumed / user_data['fats']['total']
        carbs_progress = carbs_consumed / user_data['carbs']['total']

        # Remaining amounts are already in user_data['calories']['value']
        calories_remaining = user_data['calories']['value']
        protein_remaining = user_data['protein']['value']
        fat_remaining = user_data['fats']['value']
        carbs_remaining = user_data['carbs']['value']

        # Update display values to show remaining amounts
        html_content = html_content.replace('id="caloriesValue">2199</div>', f'id="caloriesValue">{calories_remaining}</div>')
        html_content = html_content.replace('id="proteinValue">161</div>', f'id="proteinValue">{protein_remaining}g</div>')
        html_content = html_content.replace('id="carbsValue">251</div>', f'id="carbsValue">{carbs_remaining}g</div>')
        html_content = html_content.replace('id="fatsValue">61</div>', f'id="fatsValue">{fat_remaining}g</div>')

        # Update subtitles to show "Kcal Left" and "Left"
        html_content = html_content.replace('calories left</div>', 'Kcal Осталось</div>')
        html_content = html_content.replace('protein left</div>', 'Белка Ост.</div>')
        html_content = html_content.replace('carbs left</div>', 'Углеводов Ост.</div>')
        html_content = html_content.replace('fats left</div>', 'Жиров Ост.</div>')

        # Update user profile data in JavaScript
        html_content = html_content.replace(
            '''this.userProfile = {
                    goals: {
                        calories: 2500,
                        protein: 200, // grams
                        carbs: 300,   // grams
                        fats: 80      // grams
                    },
                    consumed: {
                        calories: 301,  // consumed today
                        protein: 39,    // grams consumed
                        carbs: 49,      // grams consumed
                        fats: 19        // grams consumed
                    }
                };''',
            f'''this.userProfile = {{
                    goals: {{
                        calories: {user_data['calories']['total']},
                        protein: {user_data['protein']['total']}, // grams
                        carbs: {user_data['carbs']['total']},   // grams
                        fats: {user_data['fats']['total']}      // grams
                    }},
                    consumed: {{
                        calories: {calories_consumed},  // consumed today
                        protein: {protein_consumed},    // grams consumed
                        carbs: {carbs_consumed},      // grams consumed
                        fats: {fat_consumed}        // grams consumed
                    }}
                }};'''
        )

        # Add Telegram WebApp integration
        telegram_script = f'''
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script>
            console.log('Mini app loaded with user data');

            // Telegram WebApp integration
            const tg = window.Telegram.WebApp;
            tg.expand();
            tg.ready();
            console.log('Telegram WebApp ready');

            if (tg.MainButton) {{
                tg.MainButton.setText('Loading...');
                setTimeout(() => {{
                    tg.MainButton.setText('Nutrition Dashboard');
                    console.log('Nutrition Dashboard ready');
                }}, 1000);
            }}
        </script>
        '''

        html_content = html_content.replace('</head>', f'{telegram_script}</head>')
        return html_content

    def send_html_response(self, content):
        """Send HTML response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_server(port=8080):
    """Run the HTTP server"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, RequestHandler)
    logger.info(f"🚀 Starting mini app server on port {port}")
    logger.info("📱 Available endpoints:")
    logger.info("   / - Main dashboard")
    logger.info("   /nutrition-dashboard - Nutrition dashboard")
    logger.info("   /test - Test dashboard")
    logger.info("   /health - Health check")
    logger.info("   /api/nutrition-data - JSON API for nutrition data")
    logger.info("   /api/historical-data - JSON API for historical nutrition data")
    logger.info("   /api/streak-data - JSON API for streak data")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    run_server(port)