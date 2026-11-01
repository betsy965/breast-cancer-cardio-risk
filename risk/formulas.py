"""Модуль расчёта риска радиационно-индуцированного атеросклероза.
Коэффициенты — из обзора (2020-2026):
  - ИБС: +7,4% RR на 1 Гр средней дозы на сердце
  - Инсульт: RR = 1,12 (база); дозо-зависимость сонных артерий
  - ТКИМ: +3-5% RR утолщения на 1 Гр (порог 30-35 Гр)
  - Синергия ФР: 2+ ФР -> риск x3-5
"""

import numpy as np

FR_OPTIONS = [
    "АГ",
    "СД 2 типа",
    "Дислипидемия",
    "Курение",
    "Ожирение (ИМТ>25)",
]


def fr_synergy(fr_list):
    """Синергия традиционных ФР (из статьи: 2+ ФР -> x3-5)."""
    n = len(fr_list)
    return {0: 1.0, 1: 1.5, 2: 3.0}.get(n, 5.0)


def location_factor(side, fields):
    """Левосторонняя локализация -> +22-37% RR ИБС (берём 1.30).
    Надключичное поле -> большая часть сонной артерии в поле облучения (+15%)."""
    base = 1.30 if side == "Левая" else 1.0
    if "Надключичная" in fields:
        base *= 1.15
    return base


def compute_risk(age_at_rt, side, fields, dose_heart, dose_carotid, fr_list):
    syn = fr_synergy(fr_list)
    loc = location_factor(side, fields)

    # RR ИБС (относительно женщины без ЛТ и без ФР)
    rr_ibs = (1.0 + 0.074 * dose_heart) * loc * syn
    # RR инсульта — база 1,12 + дозовый вклад сонных артерий (2%/Гр)
    rr_stroke = 1.12 * (1.0 + 0.02 * dose_carotid) * syn

    # Ожидаемый прирост ТКИМ (статья: +18-40% при 30-54 Гр -> ~0,7%/Гр)
    imt_increase_pct = min(40.0, 0.7 * dose_carotid)

    def cat(rr, dose, t_hi, t_mid, d_hi, d_mid):
        if rr >= t_hi or dose >= d_hi:
            return "ВЫСОКИЙ"
        if rr >= t_mid or dose >= d_mid:
            return "СРЕДНИЙ"
        return "НИЗКИЙ"

    cat_ibs = cat(rr_ibs, dose_heart, 3.0, 1.5, 25.0, 10.0)
    cat_stroke = cat(rr_stroke, dose_carotid, 2.5, 1.3, 35.0, 20.0)

    return {
        "rr_ibs": round(rr_ibs, 2),
        "rr_stroke": round(rr_stroke, 2),
        "cat_ibs": cat_ibs,
        "cat_stroke": cat_stroke,
        "imt_increase_pct": round(imt_increase_pct, 1),
        "imt_high_risk_threshold": dose_carotid >= 32.0,
        "age_at_rt": age_at_rt,
        "side": side,
        "fields": list(fields),
        "dose_heart": dose_heart,
        "dose_carotid": dose_carotid,
        "fr": list(fr_list),
    }