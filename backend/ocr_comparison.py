import time
import pytesseract
import easyocr
import cv2

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

TEST_IMAGES = ["clean.jpg", "degraded.jpg", "marathi_image.jpeg"]

print("=== OCR COMPARISON: Tesseract vs EasyOCR (CPU) ===\n")

# EasyOCR init (downloads models first time)
print("Loading EasyOCR (may take a minute first time)...")
reader = easyocr.Reader(["en", "hi"], gpu=False)

for img_name in TEST_IMAGES:
    print(f"\n--- {img_name} ---")
    img = cv2.imread(img_name)

    # Tesseract
    t1 = time.time()
    tess_text = pytesseract.image_to_string(img, lang="eng+mar",
                 config="--oem 3 --psm 6")
    t2 = time.time()
    print(f"Tesseract  : {t2-t1:.1f}s | chars={len(tess_text.strip())}")
    print(f"  sample: {tess_text.strip()[:80]}")

    # EasyOCR
    t3 = time.time()
    easy_result = reader.readtext(img_name, detail=0)
    easy_text = " ".join(easy_result)
    t4 = time.time()
    print(f"EasyOCR    : {t4-t3:.1f}s | chars={len(easy_text.strip())}")
    print(f"  sample: {easy_text.strip()[:80]}")

print("\nDone.")