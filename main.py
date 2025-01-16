from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from supabase import create_client, Client
from openai import AsyncOpenAI
import logging
from typing import Dict
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

# Initialize bot and dispatcher
API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize Supabase and OpenAI
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# States
class FitnessForm(StatesGroup):
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_activity = State()
    waiting_for_goal = State()

# Keyboards
gender_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]
    ],
    resize_keyboard=True
)

activity_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1.2 - Минимальный (сидячая работа)")],
        [KeyboardButton(text="1.375 - Низкий (1-3 тренировки в неделю)")],
        [KeyboardButton(text="1.55 - Умеренный (3-4 тренировки в неделю)")],
        [KeyboardButton(text="1.7 - Высокий (5-7 тренировок в неделю)")],
        [KeyboardButton(text="1.9 - Экстремальный (интенсивные тренировки)")],
    ],
    resize_keyboard=True
)

goal_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Похудеть"),
            KeyboardButton(text="Поддержание веса"),
            KeyboardButton(text="Набрать вес")
        ]
    ],
    resize_keyboard=True
)

async def save_user_data(telegram_id: int, user_data: dict, calories: int) -> bool:
    try:
        # First try to update existing record
        response = supabase.table('users')\
            .update({
                'data': user_data,
                'calories': calories
            })\
            .eq('telegram_id', telegram_id)\
            .execute()
        
        # If no record was updated (response.data is empty), insert new record
        if not response.data:
            response = supabase.table('users')\
                .insert({
                    'telegram_id': telegram_id,
                    'data': user_data,
                    'calories': calories
                })\
                .execute()
        
        return True
    except Exception as e:
        logging.error(f"Error saving to Supabase: {e}")
        return False

async def calculate_calories(data: Dict) -> float:
    base_formula = (10 * float(data['weight'])) + (6.25 * float(data['height'])) - (5 * int(data['age']))
    
    if data['gender'].lower() == 'мужской':
        base_calories = base_formula + 5
    else:
        base_calories = base_formula - 161
    
    # Apply activity multiplier
    activity_multiplier = float(data['activity'].split()[0])
    adjusted_calories = base_calories * activity_multiplier
    
    # Adjust for goal
    if data['goal'].lower() == 'похудеть':
        final_calories = adjusted_calories * 0.85  # -15%
    elif data['goal'].lower() == 'набрать вес':
        final_calories = adjusted_calories * 1.15  # +15%
    else:  # Поддержание веса
        final_calories = adjusted_calories  # No adjustment
    
    return round(final_calories)

async def get_meal_plan(calories: int) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ты - эксперт по питанию. Создай недельный план питания, уложившись в 400 слов."
                },
                {
                    "role": "user",
                    "content": f"""Создай план питания на 7 дней с дневной нормой {calories} калорий. 
                    Для каждого дня укажи:
                    - Завтрак
                    - Обед
                    - Ужин
                    
                    Для каждого приема пищи укажи КБЖУ (калории, белки, жиры, углеводы).

                    Используй следующие продукты, которые я отправлю в виде CSV таблицы:
                    
                    Продукт;Вес;Б;Ж;У;калл
Гречневая каша/Овсяная каша/Рис/Спагетти из твердых сортов;60 г (сух.вид);8,2;2,4;46;245
Зефир;50 г;0;3;40;160
Сырок глазированный;1 шт.;4;13;17;205
Лаваш тонкий или хлеб;50г;5,8;1,1;27;145
Яйцо ;2 шт.;12;11;0,7;158
Авокадо 50 или орехи 15;50/15;1;10;3;106
Бедра без шкуры или говядина (можно филе 240 г), см. инструкцию;200г;40;18,2;3;320
Хлебцы или хлеб для бутерброда;50г;5,8;1,1;27;145
Сыр твердый или ветчина;50 г;13;14;0,15;174
Филе грудки куриное без кожи;100 г;22;2;0;120
Сырники 150 г (можно покупать) или творог 9% 200 г;150г/200г;30;16;16;310
Джем к сырникам или творогу;50;0;0;32;136
Молоко 2,5% или йогурт натуральный или ряженка;200 мл;5,6;5;10;104
Овсяные хлопья или гранола;65 г;9,6;4,8;49,6;288
Шоколад ;50г;6,25;25,2;24;260
Фрукт на выбор  яблоки приоритет!;150 г;0,6;0,6;15;70
Сухофрукты;25 г;0,5;;15;70
Авокадо;100 г;2;15;2;160
Рыба белая нежирная или тунец или морепродукты;200 г;38;12;;280
Белая рыба (хек, минтай) или куриная/индюшиная грудка;100 г;19;6;;135
Печенье песочное или шоколад;50 г;3;12;31;265
Ряженка;400 мл;11,2;16;16,8;272
Бананы/хурма/виноград;150 г;2;0,38;35;155
Орехи или семена льна;25 г;3;15;3,5;157
Бананы 100 г или другие фрукты 200 г;100 г / 200 г;1,5;0,25;23;100
Гречневая каша/Овсяная каша/Рис/Спагетти из твердых сортов;60 г (сух.вид);8,2;2,4;46;245
Свежий овощ;200 г;3,2;0,4;11,2;70
Фарш говяжий (для котлет) или мясо на выбор (см. в инструкцию);150 г;24;27;10;345
Сыр твердый или полутвердый;50 г;13;14;0,15;174
;;;;;
Оливковое масло (натощак или к приему);10 мл;;9;;81
Рыба красная слабосоленая ;60 г;12;6;4;112
Йогурт сладкий;Порция 120-140 г;7,8;6,7;16,1;154
Кефир 1,5% или йогурт классический к протеину;300мл.;9;4,5;12;126
Молоко (можно безлактозное);300мл.;9;4,5;12;126
Бедра без кости иди говядина (смотреть инструкцию);200г;40;26;3;390

                    Используй следующий формат:
                    
                    ПОНЕДЕЛЬНИК:
                    Завтрак (К: X, Б: X, Ж: X, У: X)
                    
                    Обед (К: X, Б: X, Ж: X, У: X)
                    
                    Ужин (К: X, Б: X, Ж: X, У: X)
                    
                    И так далее для каждого дня недели. Уложись в 400 слов. Отправляй без markdown"""
                }
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error getting meal plan: {e}")
        return "Извините, не удалось сгенерировать план питания. Пожалуйста, попробуйте позже."

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.reply(
        "Добро пожаловать в бот Фитнес Ассистент! Давайте рассчитаем вашу дневную норму калорий.\n"
        "Для начала, выберите ваш пол:",
        reply_markup=gender_kb
    )
    await state.set_state(FitnessForm.waiting_for_gender)

@dp.message(FitnessForm.waiting_for_gender)
async def process_gender(message: types.Message, state: FSMContext):
    if message.text.lower() not in ['мужской', 'женский']:
        return await message.reply("Пожалуйста, выберите пол, используя кнопки.")
    
    await state.update_data(gender=message.text.lower())
    await message.reply("Введите ваш возраст:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FitnessForm.waiting_for_age)

@dp.message(FitnessForm.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (10 <= int(message.text) <= 120):
        return await message.reply("Пожалуйста, введите корректный возраст от 10 до 120 лет.")
    
    await state.update_data(age=message.text)
    await message.reply("Введите ваш вес в килограммах (например, 70):")
    await state.set_state(FitnessForm.waiting_for_weight)

@dp.message(FitnessForm.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text)
        if not (30 <= weight <= 300):
            raise ValueError
    except ValueError:
        return await message.reply("Пожалуйста, введите корректный вес от 30 до 300 кг.")
    
    await state.update_data(weight=message.text)
    await message.reply("Введите ваш рост в сантиметрах (например, 170):")
    await state.set_state(FitnessForm.waiting_for_height)

@dp.message(FitnessForm.waiting_for_height)
async def process_height(message: types.Message, state: FSMContext):
    try:
        height = float(message.text)
        if not (100 <= height <= 250):
            raise ValueError
    except ValueError:
        return await message.reply("Пожалуйста, введите корректный рост от 100 до 250 см.")
    
    await state.update_data(height=message.text)
    await message.reply(
        "Выберите ваш уровень физической активности:",
        reply_markup=activity_kb
    )
    await state.set_state(FitnessForm.waiting_for_activity)

@dp.message(FitnessForm.waiting_for_activity)
async def process_activity(message: types.Message, state: FSMContext):
    if not any(level in message.text for level in ['1.2', '1.375', '1.55', '1.7', '1.9']):
        return await message.reply("Пожалуйста, выберите уровень активности, используя кнопки.")
    
    await state.update_data(activity=message.text)
    await message.reply(
        "Какова ваша цель?",
        reply_markup=goal_kb
    )
    await state.set_state(FitnessForm.waiting_for_goal)

@dp.message(FitnessForm.waiting_for_goal)
async def process_goal(message: types.Message, state: FSMContext):
    if message.text not in ["Похудеть", "Поддержание веса", "Набрать вес"]:
        return await message.reply("Пожалуйста, выберите цель, используя кнопки.")
    
    await state.update_data(goal=message.text)
    user_data = await state.get_data()
    
    await message.answer("Пожалуйста, подождите, идет расчет...")
    # Calculate calories
    calories = await calculate_calories(user_data)
    
    # Get meal plan
    meal_plan = await get_meal_plan(calories)
    
    # Save to Supabase
    success = await save_user_data(message.from_user.id, user_data, calories)
    
    if not success:
        await message.reply("Предупреждение: возникла проблема с сохранением данных.")
    
    # Send results
    await message.reply(
        f"На основе предоставленной информации:\n"
        f"• Пол: {user_data['gender'].capitalize()}\n"
        f"• Возраст: {user_data['age']}\n"
        f"• Вес: {user_data['weight']} кг\n"
        f"• Рост: {user_data['height']} см\n"
        f"• Уровень активности: {user_data['activity']}\n"
        f"• Цель: {user_data['goal']}\n\n"
        f"Ваша дневная норма калорий: {calories} ккал\n\n"
        f"Вот ваш недельный план питания:\n\n{meal_plan}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="/start")]],
            resize_keyboard=True
        )
    )
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())