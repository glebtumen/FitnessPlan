from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext

from bot.states.fitness import FitnessForm
from bot.keyboards.reply import gender_kb, activity_kb, exclusions_kb, goal_kb
from bot.services.calculator import calculate_calories
from bot.services.meal_planning import get_meal_plan
from bot.database.supabase import save_user_data, check_user_access
import asyncio

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    start_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Получить план питания")],
        ],
        row_width=5,
        resize_keyboard=True,
    )

    await message.reply(
        """
Добро пожаловать в бот Фитнес Ассистент!

У меня есть следующие команды:
/start - главное меню
/pay - приобрести доступ

Для того чтобы составить план питания и рассчитать нужное количество калорий, нажмите кнопку "Получить план питания"

""",
        reply_markup=start_kb,
    )


@router.message(F.text == "Получить план питания")
async def cmd_plan(message: Message, state: FSMContext):
    # Check if user has access
    has_access = await check_user_access(message.from_user.id)
    print(has_access, flush=True)
    if not has_access:
        # Create keyboard with pay button
        pay_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="/pay")]],
            resize_keyboard=True,
        )

        await message.reply(
            "⚠️ У вас нет активного доступа к этой функции.\n\n"
            "Для получения доступа, пожалуйста, оплатите подписку, нажав на кнопку ниже:",
            reply_markup=pay_kb,
        )
        return

    # User has access, proceed with the plan
    await message.reply(
        "Давайте рассчитаем вашу дневную норму калорий и составим план питания.\n"
        "Для начала, выберите ваш пол:",
        reply_markup=gender_kb,
    )
    await state.set_state(FitnessForm.waiting_for_gender)


@router.message(FitnessForm.waiting_for_gender)
async def process_gender(message: Message, state: FSMContext):
    if message.text.lower() not in ["мужской", "женский"]:
        return await message.reply("Пожалуйста, выберите пол, используя кнопки.")

    await state.update_data(gender=message.text.lower())
    await message.reply("Введите ваш возраст:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FitnessForm.waiting_for_age)


@router.message(FitnessForm.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (10 <= int(message.text) <= 120):
        return await message.reply(
            "Пожалуйста, введите корректный возраст от 10 до 120 лет."
        )

    await state.update_data(age=message.text)
    await message.reply("Введите ваш вес в килограммах (например, 70):")
    await state.set_state(FitnessForm.waiting_for_weight)


@router.message(FitnessForm.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        if not (30 <= weight <= 300):
            raise ValueError
    except ValueError:
        return await message.reply(
            "Пожалуйста, введите корректный вес от 30 до 300 кг."
        )

    await state.update_data(weight=message.text)
    await message.reply("Введите ваш рост в сантиметрах (например, 170):")
    await state.set_state(FitnessForm.waiting_for_height)


@router.message(FitnessForm.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        if not (100 <= height <= 250):
            raise ValueError
    except ValueError:
        return await message.reply(
            "Пожалуйста, введите корректный рост от 100 до 250 см."
        )

    await state.update_data(height=message.text)
    await message.reply(
        "Выберите ваш уровень физической активности:", reply_markup=activity_kb
    )
    await state.set_state(FitnessForm.waiting_for_activity)


@router.message(FitnessForm.waiting_for_activity)
async def process_activity(message: Message, state: FSMContext):
    if not any(
        level in message.text for level in ["1.2", "1.375", "1.55", "1.7", "1.9"]
    ):
        return await message.reply(
            "Пожалуйста, выберите уровень активности, используя кнопки."
        )

    await state.update_data(activity=message.text)
    await message.reply(
        "Укажите продукты, которые следует исключить из плана питания (например: молочные продукты, орехи, морепродукты).\n"
        "Если нет исключений, нажмите соответствующую кнопку:",
        reply_markup=exclusions_kb,
    )
    await state.set_state(FitnessForm.waiting_for_exclusions)


@router.message(FitnessForm.waiting_for_exclusions)
async def process_exclusions(message: Message, state: FSMContext):
    exclusions = "Нет исключений" if message.text == "Нет исключений" else message.text
    await state.update_data(exclusions=exclusions)
    await message.reply("Какова ваша цель?", reply_markup=goal_kb)
    await state.set_state(FitnessForm.waiting_for_goal)


def split_text(text: str, chunk_size: int = 2000) -> list:
    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break

        # Ищем последний перенос строки или пробел в пределах chunk_size
        split_pos = text.rfind("\n", 0, chunk_size)
        if split_pos == -1:
            split_pos = text.rfind(" ", 0, chunk_size)

        # Если не найдено подходящее место - принудительно обрезаем
        split_pos = chunk_size if split_pos == -1 else split_pos

        chunks.append(text[:split_pos].strip())
        text = text[split_pos:].strip()

    return chunks


@router.message(FitnessForm.waiting_for_goal)
async def process_goal(message: Message, state: FSMContext):
    if message.text not in ["Похудеть", "Поддержание веса", "Набрать вес"]:
        return await message.reply("Пожалуйста, выберите цель, используя кнопки.")

    await state.update_data(goal=message.text)
    user_data = await state.get_data()

    await message.answer("Пожалуйста, подождите, идет расчет...")

    calories = await calculate_calories(user_data)
    exclusions_text = (
        ""
        if user_data["exclusions"] == "Нет исключений"
        else f"\n\nПожалуйста, исключи следующие продукты из плана: {user_data['exclusions']}"
    )
    meal_plan = await get_meal_plan(calories, exclusions_text)

    success = await save_user_data(message.from_user.id, user_data, calories)

    if not success:
        await message.reply("Предупреждение: возникла проблема с сохранением данных.")

    await message.reply(
        f"На основе предоставленной информации:\n"
        f"• Пол: {user_data['gender'].capitalize()}\n"
        f"• Возраст: {user_data['age']}\n"
        f"• Вес: {user_data['weight']} кг\n"
        f"• Рост: {user_data['height']} см\n"
        f"• Уровень активности: {user_data['activity']}\n"
        f"• Исключения: {user_data['exclusions']}\n"
        f"• Цель: {user_data['goal']}\n\n"
        f"Ваша дневная норма калорий: {calories} ккал\n\n"
    )

    # Отправка разделенного плана
    chunks = split_text(meal_plan, chunk_size=2000)

    for i, chunk in enumerate(chunks):
        reply_text = (
            f"🍏 Часть {i+1} плана питания:\n\n{chunk}"
            if len(chunks) > 1
            else f"🍏 План питания:\n\n{chunk}"
        )

        markup = (
            ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True
            )
            if i == len(chunks) - 1
            else ReplyKeyboardRemove()
        )

        await message.answer(reply_text, reply_markup=markup)
        await asyncio.sleep(0.5)  # Задержка между сообщениями

    await state.clear()

    await state.clear()
