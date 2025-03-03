from supabase import create_client
from datetime import datetime, timedelta
import logging
from config import SUPABASE_URL, SUPABASE_KEY

client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def save_user_data(telegram_id: int, user_data: dict, calories: int) -> bool:
    try:
        current_time = datetime.now().isoformat()

        response = (
            client.table("users")
            .update(
                {"data": user_data, "calories": calories, "updated_at": current_time}
            )
            .eq("telegram_id", telegram_id)
            .execute()
        )

        if not response.data:
            response = (
                client.table("users")
                .insert(
                    {
                        "telegram_id": telegram_id,
                        "data": user_data,
                        "calories": calories,
                        "created_at": current_time,
                        "updated_at": current_time,
                    }
                )
                .execute()
            )

        return True
    except Exception as e:
        logging.error(f"Error saving to Supabase: {e}")
        return False


async def update_user_access(telegram_id: int, duration: str) -> bool:
    """
    Update user access based on the selected duration.

    Args:
        telegram_id: The Telegram ID of the user
        duration: The duration of access ('1week', '1month', '3months')

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        now = datetime.now()

        if duration == "1week":
            access_to = now + timedelta(days=7)
        elif duration == "1month":
            access_to = now + timedelta(days=30)
        elif duration == "3months":
            access_to = now + timedelta(days=90)
        else:
            return False

        response = (
            client.table("users")
            .update({"access_to": access_to.isoformat(), "updated_at": now.isoformat()})
            .eq("telegram_id", telegram_id)
            .execute()
        )

        if not response.data:
            response = (
                client.table("users")
                .insert(
                    {
                        "telegram_id": telegram_id,
                        "access_to": access_to.isoformat(),
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                    }
                )
                .execute()
            )

        return True
    except Exception as e:
        logging.error(f"Error updating user access in Supabase: {e}")
        return False


async def check_user_access(telegram_id: int) -> bool:
    """
    Check if a user has active access.

    Args:
        telegram_id: The Telegram ID of the user

    Returns:
        bool: True if the user has access, False otherwise
    """
    try:
        response = (
            client.table("users")
            .select("access_to")
            .eq("telegram_id", telegram_id)
            .execute()
        )
        print(response.data, flush=True)
        if not response.data:
            return False

        access_to = response.data[0].get("access_to")

        if not access_to:
            return False

        access_to_date = datetime.fromisoformat(access_to.replace("Z", "+00:00"))
        now = datetime.now()

        return now <= access_to_date
    except Exception as e:
        logging.error(f"Error checking user access in Supabase: {e}")
        return False
