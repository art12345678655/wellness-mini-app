import asyncio
import datetime
import logging
from typing import Dict
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)


class SupabaseMiniApp:
    """Minimal Supabase client for nutrition mini app"""

    def __init__(self):
        self.client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    async def get_user_profile(self, user_telegram_id: int) -> Dict:
        """Get user's complete profile including nutrition targets - SAME AS BOT LOGIC"""
        try:
            logger.info(f"Getting user profile for user {user_telegram_id}")
            result = self.client.table('users').select('calorie_target, protein_target_g, fat_target_g, carbs_target_g').eq('user_id', user_telegram_id).execute()

            if result.data:
                logger.info(f"Found user profile: {result.data[0]}")
                return result.data[0]
            else:
                logger.warning(f"No user profile found for user {user_telegram_id}")
                return None

        except Exception as e:
            logger.exception(f"Failed to get user profile for user {user_telegram_id}: {e}")
            return None

    async def get_user_nutrition_targets(self, user_telegram_id: int) -> Dict:
        """Get user's nutrition targets."""
        try:
            result = self.client.table('users').select('calorie_target, protein_target_g, fat_target_g, carbs_target_g').eq('user_id', user_telegram_id).execute()

            if result.data:
                return result.data[0]
            else:
                logger.warning(f"No nutrition targets found for user {user_telegram_id}")
                return {
                    'calorie_target': 2000,
                    'protein_target_g': 150,
                    'fat_target_g': 65,
                    'carbs_target_g': 250
                }

        except Exception as e:
            logger.exception(f"Failed to get nutrition targets for user {user_telegram_id}: {e}")
            return {
                'calorie_target': 2000,
                'protein_target_g': 150,
                'fat_target_g': 65,
                'carbs_target_g': 250
            }

    async def get_today_nutrition_summary(self, user_telegram_id: int) -> Dict:
        """Get total nutrition consumed today."""
        return await self.get_nutrition_summary_for_date(user_telegram_id, datetime.datetime.now(datetime.timezone.utc).date())

    async def get_nutrition_summary_for_date(self, user_telegram_id: int, target_date: datetime.date) -> Dict:
        """Get total nutrition consumed for a specific date."""
        try:
            logger.info(f"Getting nutrition summary for user {user_telegram_id} on date {target_date}")

            # Query nutrition logs for the specific date
            result = self.client.table('nutrition_logs').select('total_calories, protein_g, carbs_g, fat_g').eq('user_telegram_id', user_telegram_id).gte('logged_at', target_date.isoformat()).lt('logged_at', (target_date + datetime.timedelta(days=1)).isoformat()).execute()

            # Sum up the values
            total_calories = sum(float(log.get('total_calories', 0) or 0) for log in result.data)
            total_protein = sum(float(log.get('protein_g', 0) or 0) for log in result.data)
            total_carbs = sum(float(log.get('carbs_g', 0) or 0) for log in result.data)
            total_fat = sum(float(log.get('fat_g', 0) or 0) for log in result.data)

            logger.info(f"📊 Date {target_date}: Found {len(result.data)} nutrition logs, totaling {total_calories} calories")

            return {
                'total_calories': total_calories,
                'total_protein_g': total_protein,
                'total_carbs_g': total_carbs,
                'total_fat_g': total_fat
            }

        except Exception as e:
            logger.exception(f"Failed to get nutrition summary for user {user_telegram_id} on {target_date}: {e}")
            return {
                'total_calories': 0.0,
                'total_protein_g': 0.0,
                'total_carbs_g': 0.0,
                'total_fat_g': 0.0
            }

    async def get_user_nutrition_data(self, user_telegram_id: int) -> Dict:
        """Get complete nutrition data for user (targets + consumed today)"""
        try:
            # Get targets and today's consumption
            targets = await self.get_user_nutrition_targets(user_telegram_id)
            consumed = await self.get_today_nutrition_summary(user_telegram_id)

            # Calculate remaining values
            data = {
                'calories': {
                    'value': max(0, targets.get('calorie_target', 2000) - consumed.get('total_calories', 0)),
                    'total': targets.get('calorie_target', 2000)
                },
                'protein': {
                    'value': max(0, targets.get('protein_target_g', 150) - consumed.get('total_protein_g', 0)),
                    'total': targets.get('protein_target_g', 150)
                },
                'carbs': {
                    'value': max(0, targets.get('carbs_target_g', 250) - consumed.get('total_carbs_g', 0)),
                    'total': targets.get('carbs_target_g', 250)
                },
                'fats': {
                    'value': max(0, targets.get('fat_target_g', 65) - consumed.get('total_fat_g', 0)),
                    'total': targets.get('fat_target_g', 65)
                }
            }

            logger.info(f"📊 Nutrition data for user {user_telegram_id}: {data}")
            return data

        except Exception as e:
            logger.error(f"❌ Failed to get nutrition data for user {user_telegram_id}: {e}")
            # Return default values if error
            return {
                'calories': {'value': 1500, 'total': 2000},
                'protein': {'value': 100, 'total': 150},
                'carbs': {'value': 200, 'total': 250},
                'fats': {'value': 50, 'total': 65}
            }
