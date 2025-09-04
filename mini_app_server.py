#!/usr/bin/env python3
"""
Mini App Server for Nutrition Dashboard
Standalone version with minimal dependencies for Render deployment
"""

import os
import json
import asyncio
from aiohttp import web
import logging
from supabase_db import SupabaseMiniApp
from config import PORT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MiniAppServer:
    def __init__(self):
        self.db = SupabaseMiniApp()

    async def nutrition_dashboard(self, request):
        """Serve the nutrition dashboard with real user data"""
        user_id = request.query.get('user_id')

        if not user_id:
            return web.Response(text="❌ User ID required", status=400)

        try:
            user_id = int(user_id)
            logger.info(f"📱 Mini app accessed by user {user_id}")

            # Get real user data from Supabase
            user_data = await self.db.get_user_nutrition_data(user_id)

            # Read the HTML template
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            html_file_path = os.path.join(current_dir, 'nutrition_rings.html')

            try:
                with open(html_file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            except FileNotFoundError:
                # Fallback: try to find the file in different locations
                possible_paths = [
                    'nutrition_rings.html',
                    './nutrition_rings.html',
                    '../nutrition_rings.html',
                    '/opt/render/project/src/nutrition_rings.html'
                ]
                html_content = None
                for path in possible_paths:
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                            break
                    except FileNotFoundError:
                        continue

                if html_content is None:
                    return web.Response(text="❌ HTML template not found", status=500)

            # Inject real user data
            html_content = self.inject_user_data(html_content, user_data)

            # Add Telegram WebApp integration
            telegram_script = '''
            <script src="https://telegram.org/js/telegram-web-app.js"></script>
            <script>
                const tg = window.Telegram.WebApp;
                tg.expand();
                tg.ready();

                // Send data back to bot when updated
                function sendDataToBot(data) {
                    tg.sendData(JSON.stringify(data));
                }

                // Auto-refresh data every 30 seconds
                setInterval(() => {
                    location.reload();
                }, 30000);

                // Show loading state
                console.log('Mini app loaded for user: ''' + str(user_id) + ''');
                console.log('Telegram WebApp ready:', tg);

                tg.MainButton.setText('Loading...');
                setTimeout(() => {
                    tg.MainButton.setText('Nutrition Dashboard');
                    console.log('Nutrition Dashboard ready');
                }, 1000);
            </script>
            '''

            html_content = html_content.replace('</head>', f'{telegram_script}</head>')

            logger.info(f"✅ Successfully served dashboard for user {user_id}")
            return web.Response(text=html_content, content_type='text/html')

        except Exception as e:
            logger.error(f"❌ Error serving dashboard for user {user_id}: {e}")
            return web.Response(text="❌ Error loading dashboard", status=500)

    def inject_user_data(self, html_content: str, user_data: dict) -> str:
        """Inject user data into HTML template"""
        # Update ring progress values (consumed progress)
        html_content = html_content.replace(
            'this.rings = [',
            f'''this.rings = [
                    {{ name: 'calories', color: '#E07B52', radius: 120, thickness: 20, progress: {(user_data['calories']['total'] - user_data['calories']['value']) / user_data['calories']['total']} }},
                    {{ name: 'protein', color: '#4CA6A8', radius: 100, thickness: 20, progress: {(user_data['protein']['total'] - user_data['protein']['value']) / user_data['protein']['total']} }},
                    {{ name: 'fat', color: '#FBE8A6', radius: 80, thickness: 20, progress: {(user_data['fats']['total'] - user_data['fats']['value']) / user_data['fats']['total']} }},
                    {{ name: 'carbs', color: '#A7C796', radius: 60, thickness: 20, progress: {(user_data['carbs']['total'] - user_data['carbs']['value']) / user_data['carbs']['total']} }}'''
        )

        # Update stat box values
        calories_progress = round(((user_data['calories']['total'] - user_data['calories']['value']) / user_data['calories']['total']) * 100)
        protein_progress = round(((user_data['protein']['total'] - user_data['protein']['value']) / user_data['protein']['total']) * 100)
        fats_progress = round(((user_data['fats']['total'] - user_data['fats']['value']) / user_data['fats']['total']) * 100)
        carbs_progress = round(((user_data['carbs']['total'] - user_data['carbs']['value']) / user_data['carbs']['total']) * 100)

        html_content = html_content.replace('id="caloriesStat">125%</div>', f'id="caloriesStat">{calories_progress}%</div>')
        html_content = html_content.replace('id="proteinStat">67%</div>', f'id="proteinStat">{protein_progress}%</div>')
        html_content = html_content.replace('id="fatStat">115%</div>', f'id="fatStat">{fats_progress}%</div>')
        html_content = html_content.replace('id="carbsStat">80%</div>', f'id="carbsStat">{carbs_progress}%</div>')

        # Update input values
        html_content = html_content.replace('id="caloriesInput" value="2500"', f'id="caloriesInput" value="{int(user_data["calories"]["value"])}"')
        html_content = html_content.replace('id="caloriesTarget" value="2000"', f'id="caloriesTarget" value="{int(user_data["calories"]["total"])}"')
        html_content = html_content.replace('id="proteinInput" value="80"', f'id="proteinInput" value="{int(user_data["protein"]["value"])}"')
        html_content = html_content.replace('id="proteinTarget" value="120"', f'id="proteinTarget" value="{int(user_data["protein"]["total"])}"')
        html_content = html_content.replace('id="fatInput" value="80"', f'id="fatInput" value="{int(user_data["fats"]["value"])}"')
        html_content = html_content.replace('id="fatTarget" value="70"', f'id="fatTarget" value="{int(user_data["fats"]["total"])}"')
        html_content = html_content.replace('id="carbsInput" value="200"', f'id="carbsInput" value="{int(user_data["carbs"]["value"])}"')
        html_content = html_content.replace('id="carbTarget" value="250"', f'id="carbTarget" value="{int(user_data["carbs"]["total"])}"')

        return html_content

    async def health_check(self, request):
        """Health check endpoint for Render"""
        return web.json_response({
            "status": "healthy",
            "service": "nutrition-mini-app",
            "database": "supabase",
            "timestamp": str(asyncio.get_event_loop().time())
        })

    async def api_user_data(self, request):
        """API endpoint to get user data"""
        user_id = request.match_info.get('user_id')

        if not user_id:
            return web.json_response({"error": "User ID required"}, status=400)

        try:
            user_id = int(user_id)
            data = await self.db.get_user_nutrition_data(user_id)
            return web.json_response({"status": "success", "data": data})
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def test_dashboard(self, request):
        """Test endpoint that returns a simple dashboard without user data"""
        try:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            html_file_path = os.path.join(current_dir, 'nutrition_rings.html')

            try:
                with open(html_file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            except FileNotFoundError:
                return web.Response(text=f"❌ HTML file not found at {html_file_path}", status=500)

            # Add basic Telegram WebApp integration
            telegram_script = '''
            <script src="https://telegram.org/js/telegram-web-app.js"></script>
            <script>
                console.log('Test Mini app loaded');
                const tg = window.Telegram.WebApp;
                tg.expand();
                tg.ready();
                console.log('Telegram WebApp test ready:', tg);
                tg.MainButton.setText('Test Dashboard');
            </script>
            '''

            html_content = html_content.replace('</head>', f'{telegram_script}</head>')

            logger.info("✅ Test dashboard served successfully")
            return web.Response(text=html_content, content_type='text/html')
        except Exception as e:
            logger.error(f"❌ Error serving test dashboard: {e}")
            return web.Response(text=f"❌ Test dashboard error: {str(e)}", status=500)


async def create_app():
    """Create the web application"""
    app = MiniAppServer()

    web_app = web.Application()
    web_app.router.add_get('/', app.nutrition_dashboard)
    web_app.router.add_get('/nutrition-dashboard', app.nutrition_dashboard)
    web_app.router.add_get('/test', app.test_dashboard)
    web_app.router.add_get('/health', app.health_check)
    web_app.router.add_get('/api/user/{user_id}', app.api_user_data)

    return web_app


if __name__ == '__main__':
    # For local testing and Render deployment
    web.run_app(create_app(), host='0.0.0.0', port=PORT)
