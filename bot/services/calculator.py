async def calculate_calories(data: dict) -> float:
    base_formula = (10 * float(data['weight'])) + (6.25 * float(data['height'])) - (5 * int(data['age']))
    
    if data['gender'].lower() == 'мужской':
        base_calories = base_formula + 5
    else:
        base_calories = base_formula - 161
    
    activity_multiplier = float(data['activity'].split()[0])
    adjusted_calories = base_calories * activity_multiplier
    
    if data['goal'].lower() == 'похудеть':
        final_calories = adjusted_calories * 0.85
    elif data['goal'].lower() == 'набрать вес':
        final_calories = adjusted_calories * 1.15
    else:
        final_calories = adjusted_calories
    
    return round(final_calories)