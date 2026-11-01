def build_schedule(risk_data):
    cat_ibs = risk_data["cat_ibs"]
    imt = risk_data.get("imt_mm")
    imt_high = risk_data.get("imt_high_risk_threshold", False)

    if cat_ibs == "ВЫСОКИЙ" or (imt and imt > 0.9) or imt_high:
        us_interval = "Ежегодно"
    elif cat_ibs == "СРЕДНИЙ":
        us_interval = "Каждые 2-3 года"
    else:
        us_interval = "Через 5 и 10 лет после ЛТ"

    schedule = [
        ("УЗИ сонных артерий с оценкой ТКИМ", us_interval),
        ("ЭхоКГ с оценкой GLS", "До лечения и через 6-12 мес"),
        ("Липидный профиль, АД, глюкоза", "Каждые 1-3 года"),
        ("Осмотр кардиолога", "Ежегодно"),
    ]
    if imt and imt > 1.5:
        schedule.append(("КАГ / консультация сосудистого хирурга", "Срочно"))
    return schedule

def get_recommendations(risk_data):
    recs = [
        "Статины: целевой ЛНП < 1,8 ммоль/л (при ИБС < 1,4)",
        "АД < 130/80 мм рт.ст. (иАПФ/БРА предпочтительно)",
        "HbA1c < 7% при сахарном диабете",
        "АСК 75-100 мг/сут при установленном атеросклерозе (ТКИМ>0,9, бляшки)",
        "Отказ от курения — самый эффективный шаг",
        "Аэробная нагрузка >=150 мин/нед; ИМТ < 25 кг/м2",
    ]
    return recs