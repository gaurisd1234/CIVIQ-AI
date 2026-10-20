import os

def check_image_quality(path):
    if not os.path.exists(path):
        return 0
    if not path.lower().endswith((".jpg", ".jpeg", ".png")):
        return 0
    if os.path.getsize(path) < 10 * 1024:
        return 0
    return 1