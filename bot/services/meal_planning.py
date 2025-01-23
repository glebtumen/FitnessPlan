from openai import AsyncOpenAI
import logging
from config import OPENAI_API_KEY
import json
import os

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Загружаем JSON из файла
def load_products_from_json(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Get the directory where the current script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct absolute path to products.json
products_json = load_products_from_json(os.path.join(current_dir, 'products.json'))

# Преобразуем JSON в строку для передачи в запрос
products_str = json.dumps(products_json, ensure_ascii=False)

async def get_meal_plan(calories: int, exclusions_text: str = "") -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Ты эксперт по питанию. Создай недельный план питания с точным расчетом КБЖУ."
                },
                {
                    "role": "user",
                    "content": f"""
                    Создай план питания на 7 дней ({calories} ккал/день). 
                    Требования:
                    1. Для каждого приема пищи укажи вес продуктов (не только 100 г!).
                    2. Пересчитывай КБЖУ пропорционально весу (на основе данных на 100 г).
                    3. Комбинируй продукты в блюда (например: гречка + овощи + курица).
                    4. Итоговые калории за день должны быть точно {calories} (±10 ккал).

                    Пример формата:
                    Завтрак (К: x, Б: x, Ж: x, У: x) - здесь писать уже пересчитанные данные
                     - 60 г овсянки (204 ккал, Б: 7.2, Ж: 3.6, У: 36)
                     - 1 банан (100 г, 89 ккал, Б: 1.1, Ж: 0.3, У: 22.8)
                     - 15 г орехов (86 ккал, Б: 2.6, Ж: 6.3, У: 4.6)
                     - 100 г йогурта греческого (67 ккал, Б: 8, Ж: 2, У: 4.2)

                    Доступные продукты (КБЖУ указаны на 100 г):
                    {products_str}

                    Исключить: {exclusions_text}

                    Отправляй без markdown
                    """
                }
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error: {e}")
        return "Ошибка генерации плана."