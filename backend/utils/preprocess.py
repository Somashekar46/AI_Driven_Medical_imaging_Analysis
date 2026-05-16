"""
Image preprocessing and validation utilities
"""
import io
from typing import Tuple, Dict
from PIL import Image
import numpy as np


def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
    """Validate that bytes represent a valid image file"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        return True, ""
    except Exception as e:
        return False, str(e)


def validate_medical_image(image_bytes: bytes, image_type: str = "ecg") -> Tuple[bool, str]:
    """
    Validate that image is a medical image (ECG or X-ray).

    Rules:
    - Must be a valid image file
    - Must be mostly grayscale (low color saturation)
      ECGs and X-rays are black/white/grey with minor color variations
    - Natural photos (selfies, animals, landscapes) have high color saturation → rejected

    image_type: "ecg" or "xray"
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(img)

        # 1. Size check
        h, w = img_array.shape[:2]
        if h < 50 or w < 50:
            return False, "Image is too small. Please upload a proper medical image."

        # 2. Color saturation check
        # Split into R, G, B channels
        r = img_array[:, :, 0].astype(float)
        g = img_array[:, :, 1].astype(float)
        b = img_array[:, :, 2].astype(float)

        # Calculate per-pixel color deviation
        mean_intensity = (r + g + b) / 3.0
        color_deviation = (
            np.abs(r - mean_intensity) +
            np.abs(g - mean_intensity) +
            np.abs(b - mean_intensity)
        ) / 3.0

        avg_saturation = np.mean(color_deviation)

        # Medical images (ECGs, X-rays) typically score 0-25
        # Natural photos (animals, people, nature) score 30+
        # Threshold: 28 — strict enough to reject natural photos
        #            but permissive enough for ECGs with colored grids/paper
        if avg_saturation > 10:
            if image_type == "ecg":
                return False, (
                    "This does not appear to be an ECG image. "
                    "Please upload a 12-lead ECG strip or digital ECG image."
                )
            else:
                return False, (
                    "This does not appear to be an X-ray image. "
                    "Please upload a pediatric wrist or knee X-ray image."
                )

        # 3. Check image is not pure white or pure black (blank image)
        mean_brightness = np.mean(mean_intensity)
        if mean_brightness > 252:
            return False, "Image appears to be blank (all white). Please upload a proper medical image."
        if mean_brightness < 3:
            return False, "Image appears to be blank (all black). Please upload a proper medical image."

        return True, ""

    except Exception as e:
        return False, f"Could not process image: {str(e)}"


def get_image_metadata(image_bytes: bytes) -> Dict:
    """Extract metadata from image bytes"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return {
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "size_kb": round(len(image_bytes) / 1024, 2),
        }
    except Exception:
        return {"size_kb": round(len(image_bytes) / 1024, 2)}


def preprocess_xray(image_bytes: bytes) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    for X-ray image enhancement.
    """
    import cv2
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)
    return enhanced


def normalize_ecg_image(image_bytes: bytes) -> np.ndarray:
    """
    Normalize ECG image: remove background noise, enhance signal lines.
    """
    import cv2
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    blurred = cv2.GaussianBlur(img, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return thresh
