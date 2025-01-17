from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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

exclusions_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Нет исключений")]
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