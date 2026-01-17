"""Расчёт размера сноуборда."""


def calculate_snowboard_size(
    height_cm: int,
    weight_kg: int,
    level: str,
    style: str,
) -> int:
    """
    Расчёт размера сноуборда.
    
    Формула:
    - Базовая длина: Рост × 0.88
    - Корректировка по весу: ±3 см
    - Корректировка по уровню: новичкам короче, экспертам длиннее
    - Корректировка по стилю: Фрирайд +3 см, Фристайл -3 см
    """
    # Базовая длина
    base = height_cm * 0.88
    
    # Корректировка по весу (сравниваем с "нормой" рост - 110)
    ideal_weight = height_cm - 110
    if weight_kg < ideal_weight - 5:
        weight_adjust = -3  # Лёгкий — короче
    elif weight_kg > ideal_weight + 5:
        weight_adjust = 3   # Тяжёлый — длиннее
    else:
        weight_adjust = 0
    
    # Корректировка по уровню
    if level == "Новичок":
        level_adjust = -3
    elif level == "Продвинутый":
        level_adjust = 3
    else:  # Средний
        level_adjust = 0
    
    # Корректировка по стилю
    if style == "Фрирайд":
        style_adjust = 3
    elif style == "Фристайл":
        style_adjust = -3
    else:  # Универсал
        style_adjust = 0
    
    # Итоговый размер (округляем до целого)
    result = round(base + weight_adjust + level_adjust + style_adjust)
    
    return result
