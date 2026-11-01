"""Генератор синтетического УЗИ сонной артерии для проверки сегментации.
Структура дальней стенки (сверху вниз): lumen(dark) -> intima(bright) ->
media(dark) -> adventitia(bright).  ТКИМ ~ 10 px при масштабе 0.05 мм/px = 0,5 мм.
"""
import numpy as np
import cv2

img = np.full((400, 600), 20, dtype=np.uint8)
img[150:250, 100:500] = 30    # lumen (тёмный)
img[250:253, 100:500] = 200   # intima (яркая)
img[253:260, 100:500] = 60    # media (тёмная)
img[260:275, 100:500] = 180   # adventitia (яркая)
noise = np.random.randint(0, 15, img.shape, dtype=np.uint8)
img = cv2.add(img, noise)
cv2.imwrite("synthetic_carotid.png", img)
print("Сохранено: synthetic_carotid.png — ROI: x=100, y=200, w=400, h=80, мм/px=0.05")