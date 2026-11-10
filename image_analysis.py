from PIL import Image
import numpy as np

COLOR_BUCKETS = {
    "茶色": (139, 90, 43),
    "赤": (200, 30, 30),
    "黄色": (220, 200, 60),
    "黒": (25, 25, 25),
    "無色": (240, 240, 235),
    "緑": (60, 140, 60),
    "青": (40, 80, 180),
    "紫": (120, 60, 140),
    "オレンジ": (230, 130, 40),
}

def get_dominant_color(image_path, crop_ratio=0.5):
    """画像中央付近(シミが写っている想定)の平均色を取得"""
    img = Image.open(image_path).convert("RGB")
    img = img.resize((200, 200))
    w, h = img.size
    cw, ch = int(w * crop_ratio), int(h * crop_ratio)
    left, top = (w - cw) // 2, (h - ch) // 2
    cropped = img.crop((left, top, left + cw, top + ch))
    arr = np.array(cropped).reshape(-1, 3)
    avg = arr.mean(axis=0)
    return tuple(avg)

def classify_color(rgb):
    """一番近い色バケットを返す"""
    best_name, best_dist = None, float("inf")
    for name, ref in COLOR_BUCKETS.items():
        dist = sum((a - b) ** 2 for a, b in zip(rgb, ref))
        if dist < best_dist:
            best_dist, best_name = dist, name
    return best_name