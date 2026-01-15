from dataclasses import dataclass


@dataclass
class SnowboardResult:
    min_length: int
    max_length: int
    width: str  # "" или "W" для широкой доски
    explanation: str
    tips: str


@dataclass
class SkisResult:
    min_length: int
    max_length: int
    waist: str
    radius: str
    explanation: str


def calculate_snowboard_length(
    height_cm: int,
    weight_kg: int,
    gender: str,
    shoe_size: int,
    style: str,
) -> SnowboardResult:
    """
    Расчёт размера сноуборда по таблице:
    150-160 см → 135-145 см
    160-170 см → 145-155 см
    170-180 см → 155-165 см
    180-190 см → 165-175 см
    190+ см → 175+ см
    """
    # Базовые диапазоны строго по таблице
    # 150-160 → 135-145, 160-170 → 145-155, 170-180 → 155-165, 180-190 → 165-175, 190+ → 175+
    if height_cm < 150:
        base_min, base_max = 130, 140
    elif height_cm <= 160:
        base_min, base_max = 135, 145
    elif height_cm <= 170:
        base_min, base_max = 145, 155
    elif height_cm <= 180:
        base_min, base_max = 155, 165
    elif height_cm <= 190:
        base_min, base_max = 165, 175
    else:
        base_min, base_max = 175, 185

    # Корректировка по стилю
    style_adjust = 0
    if style == "Фристайл":
        style_adjust = -3  # Для паркового катания короче
        style_note = "Фристайл — короче для трюков и манёвренности."
    elif style == "Фрирайд":
        style_adjust = 3  # Для глубокого снега длиннее
        style_note = "Фрирайд — длиннее для стабильности в пухляке."
    else:  # Универсал
        style_adjust = 0
        style_note = "Универсал — сбалансированный размер для любых условий."

    # Корректировка по полу (женские доски короче)
    gender_adjust = 0
    gender_note = ""
    if gender == "ж":
        gender_adjust = -3
        gender_note = " Женская доска короче на ~3 см."

    # Итоговые размеры
    min_length = base_min + style_adjust + gender_adjust
    max_length = base_max + style_adjust + gender_adjust

    # Широкая доска (W) для размера ноги 44+
    width = "W" if shoe_size >= 44 else ""
    width_note = ""
    if width:
        width_note = f"\n\n👟 Размер ноги {shoe_size} — нужна <b>широкая доска (W)</b>."

    explanation = f"{style_note}{gender_note}{width_note}"

    tips = (
        "💡 <b>Советы:</b>\n"
        "• Для паркового катания — на 2-5 см короче\n"
        "• Для глубокого снега — на 3-5 см длиннее\n"
        "• Между размерами: меньший = манёвренность, больший = стабильность"
    )

    return SnowboardResult(
        min_length=min_length,
        max_length=max_length,
        width=width,
        explanation=explanation,
        tips=tips,
    )


def calculate_ski_length(
    height_cm: int,
    weight_kg: int,
    level: str,
    style: str,
) -> SkisResult:
    """
    Базовая длина: рост − 10–15 см
    Корректировки по стилю, уровню и весу
    """
    base = height_cm - 12
    adjust = 0

    # Стиль
    if style == "Трасса":
        adjust -= 3
        waist = "до 75 мм"
        radius = "11–13 м"
        style_note = "Узкие лыжи для подготовленных склонов."
    elif style == "Фрирайд":
        adjust += 5
        waist = "100+ мм"
        radius = "16–22 м"
        style_note = "Широкие лыжи для целины и пухляка."
    else:  # Универсал
        adjust += 0
        waist = "75–100 мм"
        radius = "13–17 м"
        style_note = "Универсальные лыжи для любых условий."

    # Уровень
    level_note = ""
    if level == "Новичок":
        adjust -= 5
        level_note = "Укороченные для лёгкого управления."
    elif level == "Продвинутый":
        adjust += 5
        level_note = "Удлинённые для стабильности на скорости."

    # Вес
    recommended_weight = height_cm - 100
    weight_note = ""
    if weight_kg <= recommended_weight - 5:
        adjust -= 3
        weight_note = "Вес ниже среднего — укорочено."
    elif weight_kg >= recommended_weight + 5:
        adjust += 3
        weight_note = "Вес выше среднего — удлинено."

    min_length = max(base + adjust - 5, 130)
    max_length = min(base + adjust + 5, 195)

    # Собираем пояснение
    parts = [style_note]
    if level_note:
        parts.append(level_note)
    if weight_note:
        parts.append(weight_note)
    explanation = " ".join(parts)

    return SkisResult(
        min_length=min_length,
        max_length=max_length,
        waist=waist,
        radius=radius,
        explanation=explanation,
    )
