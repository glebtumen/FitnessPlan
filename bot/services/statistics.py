from datetime import datetime
from bot.database.supabase import client
import logging

async def get_basic_statistics() -> dict:
    try:
        response = client.table('users').select('*').execute()
        users_data = response.data

        if not users_data:
            return {
                "total_users": 0,
                "new_users_last_week": 0
            }

        total_users = len(users_data)
        
        current_time = datetime.now()
        week_ago = current_time.timestamp() - (7 * 24 * 60 * 60)
        last_week_users = sum(1 for user in users_data 
                            if 'created_at' in user 
                            and datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')).timestamp() > week_ago)

        return {
            "total_users": total_users,
            "new_users_last_week": last_week_users
        }
    except Exception as e:
        logging.error(f"Error getting statistics: {e}")
        return {"error": "Failed to retrieve statistics"}