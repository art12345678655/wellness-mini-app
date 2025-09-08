#!/usr/bin/env python3
"""
Simple Mini App Server for Nutrition Dashboard
Uses only standard library - no external dependencies
"""

import os
import json
import logging
import asyncio
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

class RequestHandler(BaseHTTPRequestHandler):
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

    def read_html_file(self):
        """Read the HTML template file"""
        try:
            with open('nutrition_rings.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error("❌ nutrition_rings.html not found")
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
        html_content = html_content.replace('calories left</div>', 'Kcal Left</div>')
        html_content = html_content.replace('protein left</div>', 'Left</div>')
        html_content = html_content.replace('carbs left</div>', 'Left</div>')
        html_content = html_content.replace('fats left</div>', 'Left</div>')

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
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    run_server(port)