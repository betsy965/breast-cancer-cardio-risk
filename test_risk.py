from risk.formulas import compute_risk

cases = [
    ("Низкий риск", 45, "Правая", ["Грудная стенка"], 1.5, 5.0, []),
    ("Средний риск", 55, "Левая", ["Грудная стенка"], 4.0, 25.0, ["АГ"]),
    ("Высокий риск", 50, "Левая", ["Грудная стенка", "Надключичная"], 5.0, 40.0,
     ["АГ", "Дислипидемия"]),
]

for name, *args in cases:
    r = compute_risk(*args)
    print(f"\n{name}: RR ИБС = {r['rr_ibs']}, RR инсульта = {r['rr_stroke']}")
    print(f"  Категория: {r['cat_ibs']} / {r['cat_stroke']}, "
          f"прирост ТКИМ = +{r['imt_increase_pct']}%")