import numpy as np
import cv2
from scipy.signal import find_peaks

def preprocess(image_bgr):
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)

def _profile_imt(profile, h, mm_per_px):
    profile = np.convolve(profile, np.ones(5) / 5, mode="same")
    h_start = h // 2
    seg = profile[h_start:]
    grad = np.abs(np.gradient(seg))
    peaks, props = find_peaks(
        grad, height=np.percentile(grad, 70), distance=3
    )
    if len(peaks) < 2:
        return None
    order = np.argsort(props["peak_heights"])[::-1]
    selected = sorted(peaks[order[:2]])
    imt_px = selected[1] - selected[0]
    return {
        "imt_mm": float(imt_px * mm_per_px),
        "imt_px": int(imt_px),
        "peaks_y": [h_start + int(p) for p in selected],
    }

def segment_imt(gray, roi, mm_per_px):
    x, y, w, h = roi
    roi_img = gray[y : y + h, x : x + w].astype(np.float32)
    if roi_img.size == 0:
        return None
    profile = roi_img.mean(axis=1)
    return _profile_imt(profile, h, mm_per_px)

def detect_plaque(gray, roi, mm_per_px, step_frac=30):
    x, y, w, h = roi
    step = max(1, w // step_frac)
    max_imt = 0.0
    for col in range(x, x + w, step):
        col_img = gray[y : y + h, col : col + 1].astype(np.float32)
        if col_img.size == 0:
            continue
        r = _profile_imt(col_img.mean(axis=1), h, mm_per_px)
        if r and r["imt_mm"] > max_imt:
            max_imt = r["imt_mm"]
    return round(max_imt, 2)