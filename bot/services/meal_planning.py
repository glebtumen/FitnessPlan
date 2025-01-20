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
            model="gpt-4o-mini",
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
                    4. Итоговые калории за день должны быть точно {calories} (±20 ккал).

                    Пример формата:
                    ПОНЕДЕЛЬНИК:
                    Завтрак (К: 560, Б: 17.3, Ж: 9.1, У: 93.5) 
                    - 60 г овсянки (расчет: 60г * 340 ккал/100г = 204 ккал)
                    - 1 банан (100 г, 89 ккал)
                    - 15 г орехов (15г * 572 ккал/100г = 86 ккал)

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