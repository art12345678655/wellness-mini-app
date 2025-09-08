#!/usr/bin/env python3
"""
Nutrition Mini App Server
Provides real-time nutrition data for Telegram users
"""

import os
import json
from aiohttp import web, ClientSession
from aiohttp.web import Request, Response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

# Utility function for bots to update user data
def update_user_nutrition_data(user_id, targets=None, consumed_today=None, meal_count=0):
    """
    Utility function for bots to update user nutrition data.

    Args:
        user_id (str): Telegram user ID
        targets (dict): User's daily nutrition targets
        consumed_today (dict): What user has consumed today
        meal_count (int): Number of meals logged today

    Example:
        update_user_nutrition_data(
            user_id="123456789",
            targets={'calories': 2000, 'protein_g': 150, 'fats_g': 65, 'carbs_g': 250},
            consumed_today={'calories': 450, 'protein_g': 35, 'fats_g': 15, 'carbs_g': 60},
            meal_count=2
        )
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

    print(f"Updated nutrition data for user {user_id}: {USER_DATA[user_id_str]}")
    return USER_DATA[user_id_str]

async def nutrition_dashboard(request: Request) -> Response:
    """Serve the nutrition dashboard HTML."""
    user_id = request.query.get('user_id', 'user_123')

    # Get user data
    user_data = USER_DATA.get(user_id, {
        'calories': {'value': 2199, 'total': 2500},
        'protein': {'value': 161, 'total': 200},
        'carbs': {'value': 251, 'total': 300},
        'fats': {'value': 61, 'total': 80}
    })

    # Read the HTML template
    with open('data_experiments/nutrition_rings.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Inject user data into the HTML
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
    html_content = html_content.replace('id="caloriesInput" value="2500"', f'id="caloriesInput" value="{user_data["calories"]["value"]}"')
    html_content = html_content.replace('id="caloriesTarget" value="2000"', f'id="caloriesTarget" value="{user_data["calories"]["total"]}"')
    html_content = html_content.replace('id="proteinInput" value="80"', f'id="proteinInput" value="{user_data["protein"]["value"]}"')
    html_content = html_content.replace('id="proteinTarget" value="120"', f'id="proteinTarget" value="{user_data["protein"]["total"]}"')
    html_content = html_content.replace('id="fatInput" value="80"', f'id="fatInput" value="{user_data["fats"]["value"]}"')
    html_content = html_content.replace('id="fatTarget" value="70"', f'id="fatTarget" value="{user_data["fats"]["total"]}"')
    html_content = html_content.replace('id="carbsInput" value="200"', f'id="carbsInput" value="{user_data["carbs"]["value"]}"')
    html_content = html_content.replace('id="carbTarget" value="250"', f'id="carbTarget" value="{user_data["carbs"]["total"]}"')
    
    # Add Telegram WebApp integration
    telegram_script = '''
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script>
        // Initialize Telegram WebApp
        const tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();
        
        // Send data back to bot when updated
        function sendDataToBot(data) {
            tg.sendData(JSON.stringify(data));
        }
    </script>
    '''
    
    html_content = html_content.replace('</head>', f'{telegram_script}</head>')
    
    return web.Response(text=html_content, content_type='text/html')

async def nutrition_tracker_dashboard(request: Request) -> Response:
    """Serve the nutrition tracker dashboard HTML with real data."""
    user_id = request.query.get('user_id', 'user_123')

    # Read the HTML template
    with open('data_experiments/nutritions_files.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Add user ID as a global variable for the JavaScript to access
    user_data_script = f'''
    <script>
        // User data configuration
        const USER_CONFIG = {{
            userId: '{user_id}',
            apiBaseUrl: '{request.scheme}://{request.host}'
        }};
    </script>
    '''

    # Insert the user data script before the closing </head> tag
    html_content = html_content.replace('</head>', f'{user_data_script}</head>')

    return web.Response(text=html_content, content_type='text/html')

async def api_user_data(request: Request) -> Response:
    """API endpoint to get user data."""
    user_id = request.match_info.get('user_id', 'user_123')
    user_data = USER_DATA.get(user_id, {
        'calories': {'value': 2199, 'total': 2500},
        'protein': {'value': 161, 'total': 200},
        'carbs': {'value': 251, 'total': 300},
        'fats': {'value': 61, 'total': 80}
    })
    
    return web.json_response(user_data)

async def api_update_data(request: Request) -> Response:
    """API endpoint to update user data."""
    user_id = request.match_info.get('user_id', 'user_123')

    try:
        data = await request.json()
        USER_DATA[user_id] = data

        return web.json_response({'status': 'success'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=400)

async def api_nutrition_data(request: Request) -> Response:
    """API endpoint to get real nutrition data for dashboard."""
    user_id = request.query.get('user_id', 'user_123')

    # Log the incoming request for debugging
    print(f"API Request - User ID: {user_id}")

    try:
        from config import SUPABASE_AVAILABLE

        # Check if Supabase is configured
        if SUPABASE_AVAILABLE:
            # Convert string user_id to int for database queries
            # Handle demo user IDs by mapping them to numeric values
            if user_id == 'user_123':
                user_telegram_id = 123456789  # Demo user ID
            else:
                user_telegram_id = int(user_id)

            # Import database module here to avoid circular imports
            from supabase_db import SupabaseDatabase

            # Initialize database connection
            db = SupabaseDatabase()
            await db.connect()

            # Get user's nutrition targets
            targets = await db.get_user_nutrition_targets(user_telegram_id)

            # Get today's consumed nutrition
            consumed_today = await db.get_today_nutrition_summary(user_telegram_id)

            # Calculate remaining amounts
            remaining_calories = max(0, float(targets.get('calorie_target', 2500)) - float(consumed_today.get('total_calories', 0)))
            remaining_protein = max(0, float(targets.get('protein_target_g', 200)) - float(consumed_today.get('total_protein_g', 0)))
            remaining_fats = max(0, float(targets.get('fat_target_g', 80)) - float(consumed_today.get('total_fat_g', 0)))
            remaining_carbs = max(0, float(targets.get('carbs_target_g', 300)) - float(consumed_today.get('total_carbs_g', 0)))

            # Prepare response data
            nutrition_data = {
                'user_id': user_id,
                'targets': {
                    'calories': float(targets.get('calorie_target', 2500)),
                    'protein_g': float(targets.get('protein_target_g', 200)),
                    'fats_g': float(targets.get('fat_target_g', 80)),
                    'carbs_g': float(targets.get('carbs_target_g', 300))
                },
                'consumed_today': {
                    'calories': float(consumed_today.get('total_calories', 0)),
                    'protein_g': float(consumed_today.get('total_protein_g', 0)),
                    'fats_g': float(consumed_today.get('total_fat_g', 0)),
                    'carbs_g': float(consumed_today.get('total_carbs_g', 0))
                },
                'remaining': {
                    'calories': remaining_calories,
                    'protein_g': remaining_protein,
                    'fats_g': remaining_fats,
                    'carbs_g': remaining_carbs
                },
                'progress': {
                    'calories': min(1.0, float(consumed_today.get('total_calories', 0)) / float(targets.get('calorie_target', 2500))),
                    'protein_g': min(1.0, float(consumed_today.get('total_protein_g', 0)) / float(targets.get('protein_target_g', 200))),
                    'fats_g': min(1.0, float(consumed_today.get('total_fat_g', 0)) / float(targets.get('fat_target_g', 80))),
                    'carbs_g': min(1.0, float(consumed_today.get('total_carbs_g', 0)) / float(targets.get('carbs_target_g', 300)))
                },
                'meal_count': consumed_today.get('meal_count', 0)
            }

            await db.close()
            return web.json_response(nutrition_data)
        else:
            # Use fallback demo data when Supabase is not available
            logger.info("Supabase not configured, using demo data")
            return web.json_response({
                'user_id': user_id,
                'targets': {'calories': 2500, 'protein_g': 200, 'fats_g': 80, 'carbs_g': 300},
                'consumed_today': {'calories': 301, 'protein_g': 39, 'fats_g': 19, 'carbs_g': 49},
                'remaining': {'calories': 2199, 'protein_g': 161, 'fats_g': 61, 'carbs_g': 251},
                'progress': {'calories': 0.12, 'protein_g': 0.195, 'fats_g': 0.2375, 'carbs_g': 0.1633},
                'meal_count': 1
            })

    except Exception as e:
        logger.error(f"Error fetching nutrition data for user {user_id}: {e}")
        # Return default data on error
        # Try to get real user data from in-memory storage
        real_user_data = USER_DATA.get(user_id)
        if real_user_data:
            print(f"Found real data for user {user_id}: {real_user_data}")
            return web.json_response(real_user_data)

        # Fallback to demo data
        print(f"Using demo data for user {user_id}")
        return web.json_response({
            'user_id': user_id,
            'targets': {'calories': 2500, 'protein_g': 200, 'fats_g': 80, 'carbs_g': 300},
            'consumed_today': {'calories': 301, 'protein_g': 39, 'fats_g': 19, 'carbs_g': 49},
            'remaining': {'calories': 2199, 'protein_g': 161, 'fats_g': 61, 'carbs_g': 251},
            'progress': {'calories': 0.12, 'protein_g': 0.195, 'fats_g': 0.2375, 'carbs_g': 0.1633},
            'meal_count': 1
        })

async def api_update_user_data(request: Request) -> Response:
    """API endpoint for bot to update user nutrition data."""
    try:
        data = await request.json()
        user_id = str(data.get('user_id', 'user_123'))

        # Store the real user data
        USER_DATA[user_id] = {
            'user_id': user_id,
            'targets': data.get('targets', {'calories': 2500, 'protein_g': 200, 'fats_g': 80, 'carbs_g': 300}),
            'consumed_today': data.get('consumed_today', {'calories': 0, 'protein_g': 0, 'fats_g': 0, 'carbs_g': 0}),
            'remaining': data.get('remaining', {'calories': 2500, 'protein_g': 200, 'fats_g': 80, 'carbs_g': 300}),
            'progress': data.get('progress', {'calories': 0, 'protein_g': 0, 'fats_g': 0, 'carbs_g': 0}),
            'meal_count': data.get('meal_count', 0)
        }

        print(f"Updated real data for user {user_id}: {USER_DATA[user_id]}")
        return web.json_response({'status': 'success', 'message': f'Updated data for user {user_id}'})

    except Exception as e:
        logger.error(f"Error updating user data: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=400)

def create_app():
    """Create the web application."""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/nutrition-dashboard', nutrition_dashboard)
    app.router.add_get('/nutrition-tracker', nutrition_tracker_dashboard)
    app.router.add_get('/api/user/{user_id}', api_user_data)
    app.router.add_post('/api/user/{user_id}', api_update_data)
    app.router.add_get('/api/nutrition-data', api_nutrition_data)
    app.router.add_post('/api/update-user-data', api_update_user_data)
    
    return app

if __name__ == '__main__':
    import os
    from config import PORT
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=PORT)
