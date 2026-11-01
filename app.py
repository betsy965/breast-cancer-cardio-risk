import io
import numpy as np
import pandas as pd
import cv2
import streamlit as st

from risk.formulas import compute_risk, FR_OPTIONS
from us.segment import preprocess, segment_imt, detect_plaque
from monitor.schedule import build_schedule, get_recommendations

st.set_page_config(page_title="BreastRT-CardioRisk", layout="wide")
st.title("BreastRT-CardioRisk - прототип")
st.caption(
    "Прогноз и мониторинг радиационно-индуцированного атеросклероза "
    "у пациенток после лучевой терапии РМЖ"
)

if "risk" not in st.session_state:
    st.session_state.risk = None
if "us" not in st.session_state:
    st.session_state.us = None

tab1, tab2, tab3 = st.tabs(
    ["1. Калькулятор риска", "2. Анализ УЗИ", "3. Мониторинг"]
)

# ------------------- TAB 1 -------------------
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        age = st.number_input("Возраст на момент облучения", 30, 80, 55)
        side = st.radio("Локализация опухоли", ["Левая", "Правая"], horizontal=True)
        dose_heart = st.number_input("Средняя доза на сердце, Гр", 0.0, 20.0, 3.0, 0.5)
        dose_carotid = st.number_input("Доза на сонные артерии, Гр", 0.0, 70.0, 35.0, 1.0)
    with c2:
        fields = st.multiselect(
            "Поля облучения",
            ["Грудная стенка", "Надключичная", "Парастернальная"],
            default=["Грудная стенка"],
        )
        fr_selected = st.multiselect("Традиционные ФР", FR_OPTIONS)

    if st.button("Рассчитать риск", type="primary"):
        res = compute_risk(age, side, fields, dose_heart, dose_carotid, fr_selected)
        st.session_state.risk = res
        m1, m2, m3 = st.columns(3)
        m1.metric("RR ИБС", f"{res['rr_ibs']:.2f}", res["cat_ibs"])
        m2.metric("RR инсульта", f"{res['rr_stroke']:.2f}", res["cat_stroke"])
        m3.metric("Прирост ТКИМ", f"+{res['imt_increase_pct']:.1f}%")
        if res["cat_ibs"] == "ВЫСОКИЙ" or res["cat_stroke"] == "ВЫСОКИЙ":
            st.error("Высокий риск - требуется активный кардиомониторинг")
        elif res["cat_ibs"] == "СРЕДНИЙ":
            st.warning("Средний риск - плановое наблюдение")
        else:
            st.success("Низкий риск - стандартное наблюдение")

# ------------------- TAB 2 -------------------
with tab2:
    up = st.file_uploader("Загрузите УЗИ сонной артерии (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if up is not None:
        buf = np.frombuffer(up.read(), dtype=np.uint8)
        img_bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        h, w = img_bgr.shape[:2]
        st.image(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)

        c1, c2, c3, c4, c5 = st.columns(5)
        x = c1.number_input("ROI x", 0, max(0, w - 10), w // 4)
        y = c2.number_input("ROI y", 0, max(0, h - 10), h // 3)
        ww = c3.number_input("ROI w", 10, w, w // 2)
        hh = c4.number_input("ROI h", 10, h, h // 3)
        mm_per_px = c5.number_input("мм/пиксель", 0.001, 1.0, 0.05, 0.001, format="%.4f")

        if st.button("Анализировать УЗИ", type="primary"):
            gray = preprocess(img_bgr)
            roi = (int(x), int(y), int(ww), int(hh))
            seg = segment_imt(gray, roi, mm_per_px)
            if seg is None:
                st.error("Не удалось выделить ТКИМ. Уточните ROI или масштаб.")
            else:
                plaque = detect_plaque(gray, roi, mm_per_px)
                st.session_state.us = {"imt_mm": seg["imt_mm"], "plaque": plaque}

                vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
                cv2.rectangle(
                    vis,
                    (roi[0], roi[1]),
                    (roi[0] + roi[2], roi[1] + roi[3]),
                    (0, 255, 0), 2,
                )
                for py in seg["peaks_y"]:
                    cv2.line(
                        vis,
                        (roi[0], roi[1] + py),
                        (roi[0] + roi[2], roi[1] + py),
                        (255, 0, 0), 1,
                    )
                st.image(vis, caption="ROI (зеленый) + границы ТКИМ (красные)", use_container_width=True)

                m1, m2 = st.columns(2)
                m1.metric("Средняя ТКИМ, мм", f"{seg['imt_mm']:.2f}")
                m2.metric("Макс. ТКИМ (бляшка), мм", f"{plaque:.2f}")

                if seg["imt_mm"] > 0.9:
                    st.warning("ТКИМ > 0,9 мм - субклинический атеросклероз")
                if plaque > 1.5:
                    st.error("Локальное утолщение > 1,5 мм - бляшка")

# ------------------- TAB 3 -------------------
with tab3:
    if st.session_state.risk is None:
        st.info("Сначала рассчитайте риск на вкладке 1")
    else:
        merged = dict(st.session_state.risk)
        if st.session_state.us:
            merged["imt_mm"] = st.session_state.us["imt_mm"]
            merged["plaque"] = st.session_state.us["plaque"]

        st.subheader("Персонализированный график скрининга")
        df = pd.DataFrame(build_schedule(merged), columns=["Метод", "Частота"])
        st.table(df)

        st.subheader("Рекомендации по профилактике")
        for r in get_recommendations(merged):
            st.write(f"- {r}")

        st.subheader("Клинические флаги")
        if merged.get("plaque", 0) > 1.5:
            st.error("Показана КАГ / консультация сосудистого хирурга")
        if merged["cat_ibs"] == "ВЫСОКИЙ":
            st.error("Высокий риск ИБС - ЭхоКГ с GLS, холтеровское мониторирование")

st.divider()
st.caption(
    "Прототип для научных и образовательных целей. Не является медицинским изделием. "
    "Требует клинической валидации перед применением в практике."
)