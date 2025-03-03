from openai import AsyncOpenAI
import logging
from config import OPENAI_API_KEY
import json
import os


# Загружаем JSON из файла
def load_products_from_json(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# Get the directory where the current script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct absolute path to products.json
products_json = load_products_from_json(os.path.join(current_dir, "products.json"))

# Преобразуем JSON в строку для передачи в запрос
products_str = json.dumps(products_json, ensure_ascii=False)


async def get_meal_plan(calories: int, exclusions_text: str = "") -> str:
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    try:
        completion = await client.chat.completions.create(
            model="google/gemini-2.0-pro-exp-02-05:free",
            messages=[
                {
                    "role": "system",
                    "content": "Ты эксперт по питанию. Создай недельный план питания с точным расчетом КБЖУ. План должен быть разнообразен, Комбинируй продукты, пусть человеку будет нравится есть то что ты предложил",
                },
                {
                    "role": "user",
                    "content": f"""
                    Создай план питания на 7 дней ({calories} ккал/день). 
                    Требования:
                    1. вес каждого продукта должен быть реалистичен и разнообразен, учитывай что 100 грамм круп это много.
                    2. Пересчитывай КБЖУ пропорционально весу (на основе данных на 100 г).
                    3. Комбинируй продукты в прием пищи (например: гарнир + овощи/фрукты + мясо).
                    4. Итоговые калории за день должны быть точно {calories} (±10 ккал).
                    5. План на день должен состоять из пяти приёмов пищи
                    6. Используй разный вес продуктов, не обязательно использовать ровные значения веса каждый раз
                    7. Питание должно быть разнообразно.
                    8. Исключить: {exclusions_text}


                    Пример формата:
                    Завтрак (К: x, Б: y, Ж: z, У: r) - здесь писать уже пересчитанные данные, Считай точно, без ошибок
                     - n г (продукт) (y ккал, Б: y, Ж: y, У: y)
                     - n кол-во (бананов, и тд) (x г, y ккал, Б: y, Ж: y, У: y)
                     - n г (Продукт) (y ккал, Б: y, Ж: y, У: y)
                     - n г (продукт) (y ккал, Б: y, Ж: y, У: 4.y)

                    Ниже я предоставил тебе продукты, из которых нужно составлять (КБЖУ указаны на 100 г): 
                    {products_str}

                    Исключить из рациона следующие продукты: {exclusions_text}

                    Отправляй без markdown
                    """,
                },
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error: {e}")
        return "Ошибка генерации плана."
