"""Debug acne detection - trace every step to find why acne isn't detected."""
import cv2
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.cv_analysis import (
    landmarker, TUNING_CONFIG, get_region_polygon, extract_region_mask,
    apply_white_balance, apply_clahe,
    FOREHEAD_INDICES, LEFT_CHEEK_INDICES, RIGHT_CHEEK_INDICES,
    NOSE_INDICES, CHIN_INDICES, LEFT_UNDER_EYE_INDICES, RIGHT_UNDER_EYE_INDICES
)
import mediapipe as mp

# Load test image
img_path = "face_test.png"
img_orig = cv2.imread(img_path)
h, w = img_orig.shape[:2]
print(f"Image: {w}x{h}")

# Detect face
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB))
results = landmarker.detect(mp_image)
landmarks = results.face_landmarks[0]

regions_map = {
    "forehead": FOREHEAD_INDICES,
    "left_cheek": LEFT_CHEEK_INDICES,
    "right_cheek": RIGHT_CHEEK_INDICES,
    "left_under_eye": LEFT_UNDER_EYE_INDICES,
    "right_under_eye": RIGHT_UNDER_EYE_INDICES,
    "nose": NOSE_INDICES,
    "chin": CHIN_INDICES,
}

print("\n=== COMPARISON: Before vs After Preprocessing ===\n")

for label, img_input in [("RAW (no preprocessing)", img_orig.copy()),
                          ("AFTER white_balance + CLAHE", None)]:
    if img_input is None:
        img_input = apply_white_balance(img_orig.copy())
        img_lab = cv2.cvtColor(img_input, cv2.COLOR_BGR2LAB)
        img_lab = apply_clahe(img_lab)
        # Use the CLAHE-corrected LAB directly
        a_channel = img_lab[:, :, 1]
    else:
        img_lab = cv2.cvtColor(img_input, cv2.COLOR_BGR2LAB)
        a_channel = img_lab[:, :, 1]

    print(f"--- {label} ---")
    total_acne = 0

    for name, indices in regions_map.items():
        poly = get_region_polygon(landmarks, indices, w, h)
        mask = extract_region_mask(img_input, poly)
        area = np.sum(mask == 255)
        if area == 0:
            continue

        mean_a, std_a = cv2.meanStdDev(a_channel, mask=mask)
        mean_a, std_a = mean_a[0][0], std_a[0][0]

        # Current threshold
        threshold_current = max(
            mean_a + TUNING_CONFIG["acne_std_multiplier"] * std_a,
            mean_a + TUNING_CONFIG["acne_min_redness_offset"]
        )

        # More aggressive thresholds to test
        threshold_aggressive = max(
            mean_a + 1.8 * std_a,
            mean_a + 6.0
        )

        red_spots = cv2.bitwise_and(a_channel, a_channel, mask=mask)

        # Count with current threshold
        _, spot_mask = cv2.threshold(red_spots, threshold_current, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(spot_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        current_count = sum(1 for c in contours if TUNING_CONFIG["acne_min_contour_area"] < cv2.contourArea(c) < TUNING_CONFIG["acne_max_contour_area"])

        # Count with aggressive threshold
        _, spot_mask2 = cv2.threshold(red_spots, threshold_aggressive, 255, cv2.THRESH_BINARY)
        contours2, _ = cv2.findContours(spot_mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        aggressive_count = sum(1 for c in contours2 if 2 < cv2.contourArea(c) < 200)

        # Count ALL red pixels above various thresholds
        pixels_above_mean_5 = np.sum(red_spots[mask == 255] > mean_a + 5)
        pixels_above_mean_8 = np.sum(red_spots[mask == 255] > mean_a + 8)
        pixels_above_mean_10 = np.sum(red_spots[mask == 255] > mean_a + 10)

        # Show the max a* value in the region
        region_a_vals = a_channel[mask == 255]
        max_a = np.max(region_a_vals) if len(region_a_vals) > 0 else 0
        p95_a = np.percentile(region_a_vals, 95) if len(region_a_vals) > 0 else 0
        p99_a = np.percentile(region_a_vals, 99) if len(region_a_vals) > 0 else 0

        print(f"  {name:20s}: mean_a={mean_a:.1f}, std_a={std_a:.1f}, max_a={max_a:.0f}, "
              f"p95={p95_a:.1f}, p99={p99_a:.1f}, "
              f"threshold={threshold_current:.1f}, "
              f"spots_current={current_count}, spots_aggressive={aggressive_count}, "
              f"px>mean+5={pixels_above_mean_5}, px>mean+8={pixels_above_mean_8}")
        total_acne += current_count

    print(f"  TOTAL acne spots (current): {total_acne}")
    print()
