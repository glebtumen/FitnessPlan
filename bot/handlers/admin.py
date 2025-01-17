from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import ADMIN_IDS
from bot.services.statistics import get_basic_statistics

router = Router()

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("У вас нет доступа к этой команде.")
        return

    await message.answer("Собираю статистику...")
    
    stats = await get_basic_statistics()
    
    if "error" in stats:
        await message.reply("Ошибка при получении статистики. Попробуйте позже.")
        return

    stats_message = (
        "📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"📈 Новых пользователей за неделю: {stats['new_users_last_week']}"
    )

    await message.reply(stats_message)