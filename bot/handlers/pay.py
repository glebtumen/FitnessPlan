from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram import Bot
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ContentType, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from bot.database.supabase import update_user_access
import logging
from .user import cmd_start

from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

router = Router()

ADMIN_ID = 409472138  # Hardcoded admin ID


class PayStates(StatesGroup):
    select_payment_method = State()
    show_bank_transfer_details = State()
    send_cheque = State()


@router.message(Command("pay"))
async def process_pay_command(message: types.Message, state: FSMContext) -> None:
    bank_payment_details = """Альфа - 3123123
Тиньк - 1231321"""

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="🔗 Проверить оплату", callback_data="check_payment"
        )
    )
    # builder.row(
    #     types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    # )
    # builder.row(types.InlineKeyboardButton(text="🚫 Закрыть", callback_data="cancel"))

    await message.answer(
        f"""Стоимость:

1 неделя - 300 RUB
1 месяц - 750 RUB
3 месяца - 2000 RUB

Для оплаты банковским переводом:

1. Переведите (без комментария) необходимую сумму по следующим реквизитам:
{bank_payment_details}

2. Нажмите на кнопку проверки оплаты ниже:
""",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "check_payment")
async def send_cheque(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.answer(
        "Отправьте скриншот страницы перевода (чек) в виде фотографии или документа."
    )
    await state.set_state(PayStates.send_cheque)


@router.message(PayStates.send_cheque)
async def cheque_handler(message: Message, state: FSMContext) -> None:
    bot: Bot = message.bot

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="1 неделя", callback_data=f"approve_1week_{message.from_user.id}"
        ),
        types.InlineKeyboardButton(
            text="1 месяц", callback_data=f"approve_1month_{message.from_user.id}"
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text="3 месяца", callback_data=f"approve_3months_{message.from_user.id}"
        ),
        types.InlineKeyboardButton(
            text="Отклонить", callback_data=f"decline_{message.from_user.id}"
        ),
    )

    if message.content_type == "photo":
        await bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"{message.from_user.full_name} (ID: {message.from_user.id})",
            reply_markup=builder.as_markup(),
        )
    elif message.content_type == "document":
        await bot.send_document(
            ADMIN_ID,
            message.document.file_id,
            caption=f"{message.from_user.full_name} (ID: {message.from_user.id})",
            reply_markup=builder.as_markup(),
        )

    await message.answer("Чек успешно загружен, ожидайте ответа администратора.")
    await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_handler(
    callback_query: types.CallbackQuery, state: FSMContext
) -> None:
    await callback_query.message.answer("Операция отменена.")
    await state.clear()


@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback_query: types.CallbackQuery) -> None:
    # Extract data from callback
    parts = callback_query.data.split("_")
    if len(parts) != 3:
        await callback_query.answer("Ошибка в данных колбэка")
        return

    duration = parts[1]  # 1week, 1month, or 3months
    user_id = int(parts[2])

    # Update user access in database
    success = await update_user_access(user_id, duration)

    if success:
        duration_text = {
            "1week": "1 неделю",
            "1month": "1 месяц",
            "3months": "3 месяца",
        }.get(duration, duration)

        # Notify admin
        await callback_query.message.answer(
            f"✅ Доступ предоставлен на {duration_text}.\n\n"
            f"Пользователь: ID {user_id}"
        )

        # Notify user
        try:
            start_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Получить план питания")],
                ],
                row_width=5,
                resize_keyboard=True,
            )

            await callback_query.bot.send_message(
                user_id,
                f'✅ Ваш платеж подтвержден! Доступ предоставлен на {duration_text}. Для того чтобы составить план питания и рассчитать нужное количество калорий, нажмите кнопку "Получить план питания"',
                reply_markup=start_kb,
            )
            await cmd_start(Message)
        except Exception as e:
            logging.error(f"Failed to notify user {user_id}: {e}")
    else:
        await callback_query.message.answer(
            f"❌ Ошибка при обновлении доступа для пользователя ID {user_id}."
        )

    await callback_query.answer()


@router.callback_query(F.data.startswith("decline_"))
async def decline_payment(callback_query: types.CallbackQuery) -> None:
    # Extract user ID from callback
    parts = callback_query.data.split("_")
    if len(parts) != 2:
        await callback_query.answer("Ошибка в данных колбэка")
        return

    user_id = int(parts[1])

    # Notify admin
    await callback_query.message.answer(
        f"❌ Платеж отклонен.\n\n" f"Пользователь: ID {user_id}"
    )

    # Notify user
    try:
        await callback_query.bot.send_message(
            user_id,
            "❌ Ваш платеж отклонен. Пожалуйста, свяжитесь с администратором @oslsldododo для уточнения деталей.",
        )
    except Exception as e:
        logging.error(f"Failed to notify user {user_id}: {e}")

    await callback_query.answer()
