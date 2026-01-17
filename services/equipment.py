"""Расчёт размера сноуборда."""


def calculate_snowboard_size(
    gender: str,
    weight_kg: int,
    style: str,
) -> int:
    """
    Расчёт размера сноуборда.
    
    Формула:
    - Мужчины: 0.3 × вес + 136
    - Женщины: 0.4 × вес + 127
    
    Корректировка по стилю:
    - Фрирайд: +3 см
    - Фристайл: -3 см
    - Универсал: без изменений
    """
    # Базовая длина по полу и весу
    if gender == "м":
        base = 0.3 * weight_kg + 136
    else:  # ж
        base = 0.4 * weight_kg + 127
    
    # Корректировка по стилю
    if style == "Фрирайд":
        style_adjust = 3
    elif style == "Фристайл":
        style_adjust = -3
    else:  # Универсал
        style_adjust = 0
    
    # Итоговый размер (округляем до целого)
    result = round(base + style_adjust)
    
    return result
