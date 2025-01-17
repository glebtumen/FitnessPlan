from supabase import create_client
from datetime import datetime
import logging
from config import SUPABASE_URL, SUPABASE_KEY

client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def save_user_data(telegram_id: int, user_data: dict, calories: int) -> bool:
    try:
        current_time = datetime.now().isoformat()
        
        response = client.table('users')\
            .update({
                'data': user_data,
                'calories': calories,
                'updated_at': current_time
            })\
            .eq('telegram_id', telegram_id)\
            .execute()
        
        if not response.data:
            response = client.table('users')\
                .insert({
                    'telegram_id': telegram_id,
                    'data': user_data,
                    'calories': calories,
                    'created_at': current_time,
                    'updated_at': current_time
                })\
                .execute()
        
        return True
    except Exception as e:
        logging.error(f"Error saving to Supabase: {e}")
        return False