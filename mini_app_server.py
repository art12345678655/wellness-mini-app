#!/usr/bin/env python3
"""
Simple Mini App Server for Nutrition Dashboard
Uses only standard library - no external dependencies
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseMiniApp:
    """Simple mock Supabase client"""
    def __init__(self):
        pass

    def get_user_nutrition_data(self, user_id: str) -> dict:
        """Get mock nutrition data"""
        logger.info(f"Getting nutrition data for user {user_id}")

        # Mock data - replace with real Supabase calls later
        return {
            'calories': {'value': 1500, 'total': 2000},
            'protein': {'value': 80, 'total': 150},
            'carbs': {'value': 200, 'total': 250},
            'fats': {'value': 50, 'total': 65}
        }

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

    def handle_nutrition_dashboard(self, query_params):
        """Serve the nutrition dashboard"""
        user_id = query_params.get('user_id', [None])[0]

        if not user_id:
            self.send_error(400, "User ID required")
            return

        try:
            logger.info(f"📱 Mini app accessed by user {user_id}")

            # Get user data
            db = SupabaseMiniApp()
            user_data = db.get_user_nutrition_data(user_id)

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
        calories_progress = user_data['calories']['value'] / user_data['calories']['total']
        protein_progress = user_data['protein']['value'] / user_data['protein']['total']
        fat_progress = user_data['fats']['value'] / user_data['fats']['total']
        carbs_progress = user_data['carbs']['value'] / user_data['carbs']['total']

        # Calculate remaining amounts (goal - consumed)
        calories_remaining = user_data['calories']['total'] - user_data['calories']['value']
        protein_remaining = user_data['protein']['total'] - user_data['protein']['value']
        fat_remaining = user_data['fats']['total'] - user_data['fats']['value']
        carbs_remaining = user_data['carbs']['total'] - user_data['carbs']['value']

        # Update display values to show remaining amounts
        html_content = html_content.replace('id="caloriesValue">2199</div>', f'id="caloriesValue">{calories_remaining}</div>')
        html_content = html_content.replace('id="proteinValue">161</div>', f'id="proteinValue">{protein_remaining}g</div>')
        html_content = html_content.replace('id="carbsValue">251</div>', f'id="carbsValue">{carbs_remaining}g</div>')
        html_content = html_content.replace('id="fatsValue">61</div>', f'id="fatsValue">{fat_remaining}g</div>')

        # Update subtitles to show consumed amounts
        html_content = html_content.replace('calories left</div>', f'{user_data["calories"]["value"]} cal consumed</div>')
        html_content = html_content.replace('protein left</div>', f'{user_data["protein"]["value"]}g consumed</div>')
        html_content = html_content.replace('carbs left</div>', f'{user_data["carbs"]["value"]}g consumed</div>')
        html_content = html_content.replace('fats left</div>', f'{user_data["fats"]["value"]}g consumed</div>')

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
                        calories: {user_data['calories']['value']},  // consumed today
                        protein: {user_data['protein']['value']},    // grams consumed
                        carbs: {user_data['carbs']['value']},      // grams consumed
                        fats: {user_data['fats']['value']}        // grams consumed
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