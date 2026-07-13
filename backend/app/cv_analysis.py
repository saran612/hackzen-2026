import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from fastapi import HTTPException
import logging
import os

logger = logging.getLogger(__name__)

# Initialize MediaPipe Face Landmarker Tasks API
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task")
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    num_faces=4  # Detect up to 4 to handle multi-face warning
)
landmarker = vision.FaceLandmarker.create_from_options(options)

# --- COMPUTER VISION HEURISTICS TUNING CONFIG ---
TUNING_CONFIG = {
    # 1. Acne / Blemishes Heuristics
    "acne_std_multiplier": 1.8,
    "acne_min_redness_offset": 3.5,
    "acne_min_contour_area": 2,
    "acne_max_contour_area": 250,
    "acne_score_multiplier": 6.0,

    # 2. Dark Circles Heuristics
    "dark_circles_multiplier": 450.0,

    # 3. Hyperpigmentation / Uneven Tone Heuristics
    "pigmentation_offset": 12.0,
    "pigmentation_multiplier": 8.0,

    # 4. Wrinkles / Fine Lines Heuristics
    "wrinkle_canny_low": 80,
    "wrinkle_canny_high": 180,
    "wrinkle_density_offset": 0.008,
    "wrinkle_score_multiplier": 3500.0,

    # 5. Oiliness Heuristics
    "oiliness_v_threshold": 238,
    "oiliness_s_threshold": 45,
    "oiliness_score_multiplier": 4000.0,

    # 6. Dryness Heuristics
    "dryness_base_offset": 40.0,
    "dryness_base_multiplier": 0.3,
    "dryness_oiliness_reduction": 0.5,

    # 7. Quality Gates
    "min_resolution": 200,
    "max_yaw_degrees": 30.0,
    "max_pitch_degrees": 25.0,
    "exposure_clip_threshold": 0.15,
    "lighting_cv_threshold": 0.20,
    "flash_spot_max_area": 50,
    "flash_spot_v_threshold": 250,
}


# Landmark Indices for Regions
FOREHEAD_INDICES = [10, 338, 297, 332, 284, 251, 21, 54, 103, 67, 109, 168, 8, 9, 336]
LEFT_CHEEK_INDICES = [116, 123, 147, 213, 192, 214, 212, 135, 136, 150, 149, 176, 148]
RIGHT_CHEEK_INDICES = [345, 352, 376, 433, 416, 434, 432, 364, 365, 379, 378, 400]
LEFT_UNDER_EYE_INDICES = [111, 116, 117, 118, 119, 120, 143, 110, 228, 229, 230]
RIGHT_UNDER_EYE_INDICES = [340, 345, 346, 347, 348, 349, 372, 448, 449, 450]
NOSE_INDICES = [168, 6, 197, 195, 5, 4, 1, 98, 327, 326, 97, 220, 440]
CHIN_INDICES = [152, 377, 400, 378, 379, 365, 397, 288, 361, 321, 405, 314, 17, 84, 181, 91, 146, 61, 81, 179]


def get_region_polygon(landmarks, indices, img_w, img_h):
    """Helper to convert landmark indices into image pixel coordinate polygon."""
    points = []
    for idx in indices:
        if idx < len(landmarks):
            pt = landmarks[idx]
            points.append([int(pt.x * img_w), int(pt.y * img_h)])
    return np.array(points, dtype=np.int32)


def extract_region_mask(img, polygon):
    """Helper to create a binary mask for a region."""
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [polygon], 255)
    return mask


# ---------------------------------------------------------------------------
# Preprocessing helpers
# ---------------------------------------------------------------------------

def apply_white_balance(img_bgr):
    """Gray-world white balance correction to neutralize color casts."""
    result = img_bgr.copy().astype(np.float32)
    avg_b = np.mean(result[:, :, 0])
    avg_g = np.mean(result[:, :, 1])
    avg_r = np.mean(result[:, :, 2])
    avg_gray = (avg_b + avg_g + avg_r) / 3.0
    if avg_b > 0:
        result[:, :, 0] *= avg_gray / avg_b
    if avg_g > 0:
        result[:, :, 1] *= avg_gray / avg_g
    if avg_r > 0:
        result[:, :, 2] *= avg_gray / avg_r
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_clahe(img_lab):
    """Apply CLAHE to the L* channel for uneven lighting normalization."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_lab[:, :, 0] = clahe.apply(img_lab[:, :, 0])
    return img_lab


def check_exposure(l_channel, face_mask):
    """Check for over/underexposure within the face region."""
    face_pixels = l_channel[face_mask == 255]
    if len(face_pixels) == 0:
        return "normal"
    total = len(face_pixels)
    underexposed_ratio = np.sum(face_pixels < 15) / total
    overexposed_ratio = np.sum(face_pixels > 240) / total
    threshold = TUNING_CONFIG["exposure_clip_threshold"]
    if underexposed_ratio > threshold:
        return "underexposed"
    if overexposed_ratio > threshold:
        return "overexposed"
    return "normal"


def check_lighting_uniformity(zone_mean_ls):
    """Check if lighting across face zones is even using coefficient of variation."""
    if len(zone_mean_ls) < 3:
        return "unknown"
    arr = np.array(zone_mean_ls)
    mean_val = np.mean(arr)
    if mean_val == 0:
        return "unknown"
    cv_val = np.std(arr) / mean_val
    if cv_val > TUNING_CONFIG["lighting_cv_threshold"]:
        return "uneven"
    return "good"


def detect_flash(img_hsv, face_mask):
    """Detect flash photography via sharp, small, very bright specular clusters."""
    hsv_v = img_hsv[:, :, 2]
    hsv_s = img_hsv[:, :, 1]
    flash_mask = cv2.bitwise_and(
        cv2.compare(hsv_v, TUNING_CONFIG["flash_spot_v_threshold"], cv2.CMP_GT),
        cv2.compare(hsv_s, 20, cv2.CMP_LT)
    )
    flash_in_face = cv2.bitwise_and(flash_mask, flash_mask, mask=face_mask)
    contours, _ = cv2.findContours(flash_in_face, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    small_bright_clusters = 0
    for c in contours:
        area = cv2.contourArea(c)
        if 2 < area < TUNING_CONFIG["flash_spot_max_area"]:
            small_bright_clusters += 1
    return small_bright_clusters >= 3


def compute_face_pose(landmarks, img_w, img_h):
    """Estimate face yaw and pitch from landmark geometry."""
    def px(idx):
        pt = landmarks[idx]
        return pt.x * img_w, pt.y * img_h

    nose_x, nose_y = px(1)
    left_x, _ = px(234)
    right_x, _ = px(454)
    _, top_y = px(10)
    _, chin_y = px(152)

    face_width = abs(right_x - left_x)
    if face_width < 1:
        return 0.0, 0.0

    # Yaw: how far the nose is off-center between the face edges
    face_center_x = (left_x + right_x) / 2.0
    yaw_offset = (nose_x - face_center_x) / (face_width / 2.0)
    yaw_degrees = yaw_offset * 45.0

    # Pitch: ratio of forehead-to-nose vs nose-to-chin vertical distance
    forehead_to_nose = abs(nose_y - top_y)
    face_height = abs(chin_y - top_y)
    if face_height < 1:
        return round(yaw_degrees, 1), 0.0
    expected_ratio = 0.6
    actual_ratio = forehead_to_nose / face_height
    pitch_offset = (actual_ratio - expected_ratio) / 0.3
    pitch_degrees = pitch_offset * 30.0

    return round(yaw_degrees, 1), round(pitch_degrees, 1)


def select_largest_face(results, img_w, img_h):
    """From multiple detected faces, select the one with the largest bounding area."""
    best_idx = 0
    best_area = 0
    for i, landmarks in enumerate(results.face_landmarks):
        xs = [pt.x * img_w for pt in landmarks]
        ys = [pt.y * img_h for pt in landmarks]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if area > best_area:
            best_area = area
            best_idx = i
    return best_idx, best_area


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_skin_image(image_bytes: bytes):
    """
    Full CV analysis pipeline with input hardening, quality checks,
    preprocessing corrections, and per-score confidence.

    Returns: (scores, regions, quality, warnings)
    """
    # --- 1. Decode & validate ---
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file format. Please upload a valid JPEG or PNG image.")

    h, w, _ = img.shape

    # Minimum resolution gate
    if h < TUNING_CONFIG["min_resolution"] or w < TUNING_CONFIG["min_resolution"]:
        raise HTTPException(
            status_code=400,
            detail=f"Image resolution too low ({w}x{h}). Please upload an image at least {TUNING_CONFIG['min_resolution']}x{TUNING_CONFIG['min_resolution']}px for accurate analysis."
        )

    # --- 2. Face detection ---
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    results = landmarker.detect(mp_image)

    if not results.face_landmarks:
        raise HTTPException(
            status_code=400,
            detail="No face detected. Please ensure your face is clearly visible, well-lit, and at a frontal angle."
        )

    warnings = []
    faces_detected = len(results.face_landmarks)

    if faces_detected > 1:
        best_idx, _ = select_largest_face(results, w, h)
        warnings.append(f"Multiple faces detected ({faces_detected}) — analyzing the largest face.")
    else:
        best_idx = 0

    landmarks = results.face_landmarks[best_idx]

    # --- 3. Face pose check ---
    yaw_deg, pitch_deg = compute_face_pose(landmarks, w, h)
    angle_is_extreme = (abs(yaw_deg) > TUNING_CONFIG["max_yaw_degrees"] or
                        abs(pitch_deg) > TUNING_CONFIG["max_pitch_degrees"])
    if angle_is_extreme:
        warnings.append(
            f"Face angle may be too extreme (yaw: {yaw_deg}, pitch: {pitch_deg}). "
            "Scores are provided but confidence is reduced. For best results, face the camera directly."
        )

    # --- 4. Compute face bounding area ---
    xs = [pt.x * w for pt in landmarks]
    ys = [pt.y * h for pt in landmarks]
    face_area_px = int((max(xs) - min(xs)) * (max(ys) - min(ys)))
    face_height_px = int(max(ys) - min(ys))

    # --- 5. Preprocessing ---
    preprocessing_applied = []
    img = apply_white_balance(img)
    preprocessing_applied.append("white_balance")

    # --- 6. Region segmentation ---
    regions = {
        "forehead": get_region_polygon(landmarks, FOREHEAD_INDICES, w, h),
        "left_cheek": get_region_polygon(landmarks, LEFT_CHEEK_INDICES, w, h),
        "right_cheek": get_region_polygon(landmarks, RIGHT_CHEEK_INDICES, w, h),
        "left_under_eye": get_region_polygon(landmarks, LEFT_UNDER_EYE_INDICES, w, h),
        "right_under_eye": get_region_polygon(landmarks, RIGHT_UNDER_EYE_INDICES, w, h),
        "nose": get_region_polygon(landmarks, NOSE_INDICES, w, h),
        "chin": get_region_polygon(landmarks, CHIN_INDICES, w, h),
    }

    regions_serializable = {name: poly.tolist() for name, poly in regions.items()}

    # Combined face mask for quality checks
    face_mask = np.zeros(img.shape[:2], dtype=np.uint8)
    for poly in regions.values():
        cv2.fillPoly(face_mask, [poly], 255)

    # --- 7. Color space conversions ---
    img_lab_raw = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # Preserve pre-CLAHE a* and L* channels (CLAHE modifies the L* channel in-place)
    a_channel_raw = img_lab_raw[:, :, 1].copy()
    l_channel_raw = img_lab_raw[:, :, 0].copy()

    # Exposure check (before CLAHE)
    exposure_status = check_exposure(l_channel_raw, face_mask)
    if exposure_status != "normal":
        warnings.append(f"Image appears {exposure_status}. Auto-correction applied, but scores may have reduced accuracy.")

    # CLAHE normalization (for luminance-based heuristics: pigmentation, dark circles, wrinkles)
    img_lab = apply_clahe(img_lab_raw)
    preprocessing_applied.append("clahe")

    img_corrected = cv2.cvtColor(img_lab, cv2.COLOR_LAB2BGR)
    img_hsv = cv2.cvtColor(img_corrected, cv2.COLOR_BGR2HSV)
    img_gray = cv2.cvtColor(img_corrected, cv2.COLOR_BGR2GRAY)

    # --- 8. Flash detection ---
    flash_detected = detect_flash(img_hsv, face_mask)
    if flash_detected:
        warnings.append("Flash photography detected. Oiliness score may be inflated — confidence for oiliness is reduced.")

    # --- 9. Cheek baseline & lighting uniformity ---
    cheek_masks = [extract_region_mask(img, regions[n]) for n in ["left_cheek", "right_cheek"]]
    combined_cheek_mask = cv2.bitwise_or(cheek_masks[0], cheek_masks[1])
    cheek_mean_l = cv2.mean(l_channel_raw, mask=combined_cheek_mask)[0]

    zone_mean_ls = []
    for name, poly in regions.items():
        zmask = extract_region_mask(img, poly)
        zml = cv2.mean(l_channel_raw, mask=zmask)[0]
        zone_mean_ls.append(zml)

    lighting_uniformity = check_lighting_uniformity(zone_mean_ls)
    if lighting_uniformity == "uneven":
        warnings.append("Lighting appears uneven across your face. Scores (especially under-eye contrast) may be less accurate.")

    # --- 10. Initialize confidence ---
    raw_scores = {
        "acne": 0, "under_eye_contrast": 0, "pigmentation": 0,
        "oiliness": 0, "dryness": 0, "wrinkles": 0,
        "redness": 0, "t_zone_oiliness": 0, "cheek_oiliness": 0,
    }

    base_confidence = "high"
    if angle_is_extreme:
        base_confidence = "low"
    elif exposure_status != "normal" or lighting_uniformity == "uneven":
        base_confidence = "medium"

    per_score_confidence = {k: base_confidence for k in raw_scores}
    if flash_detected:
        per_score_confidence["oiliness"] = "low"
        per_score_confidence["t_zone_oiliness"] = "low"
        per_score_confidence["cheek_oiliness"] = "low"
    if lighting_uniformity == "uneven":
        per_score_confidence["under_eye_contrast"] = "low"

    # --- 11. Per-region heuristic analysis ---
    acne_count = 0
    total_skin_pixels = 0
    wrinkle_pixel_count = 0
    wrinkle_analyzed_pixels = 0
    tone_std_devs = []
    # Use pre-CLAHE a* channel for acne — CLAHE normalizes away redness peaks
    a_channel = a_channel_raw

    wrinkle_assessable = face_height_px >= TUNING_CONFIG["min_resolution"]
    if not wrinkle_assessable:
        per_score_confidence["wrinkles"] = "low"

    for name, poly in regions.items():
        mask = extract_region_mask(img, poly)
        area = np.sum(mask == 255)
        if area == 0:
            continue
        total_skin_pixels += area

        # 1. ACNE / BLEMISHES
        mean_a, std_a = cv2.meanStdDev(a_channel, mask=mask)
        mean_a, std_a = mean_a[0][0], std_a[0][0]
        red_threshold = max(
            mean_a + TUNING_CONFIG["acne_std_multiplier"] * std_a,
            mean_a + TUNING_CONFIG["acne_min_redness_offset"]
        )
        red_spots = cv2.bitwise_and(a_channel, a_channel, mask=mask)
        _, spot_mask = cv2.threshold(red_spots, red_threshold, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(spot_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            c_area = cv2.contourArea(c)
            if TUNING_CONFIG["acne_min_contour_area"] < c_area < TUNING_CONFIG["acne_max_contour_area"]:
                acne_count += 1

        # 2. PIGMENTATION / UNEVEN TONE
        if name in ["forehead", "left_cheek", "right_cheek"]:
            _, std_l = cv2.meanStdDev(l_channel_raw, mask=mask)
            tone_std_devs.append(std_l[0][0])

        # 3. WRINKLES / FINE LINES
        if wrinkle_assessable:
            kernel = np.ones((5, 5), np.uint8)
            eroded_mask = cv2.erode(mask, kernel, iterations=3)
            eroded_area = np.sum(eroded_mask == 255)
            if eroded_area > 0:
                smoothed_gray = cv2.bilateralFilter(img_gray, 5, 50, 50)
                edges = cv2.Canny(smoothed_gray, TUNING_CONFIG["wrinkle_canny_low"], TUNING_CONFIG["wrinkle_canny_high"])
                region_edges = cv2.bitwise_and(edges, edges, mask=eroded_mask)
                edge_count = np.sum(region_edges > 0)
                wrinkle_pixel_count += edge_count
                wrinkle_analyzed_pixels += eroded_area

    # --- 12. Calculate Final Scores (0-100) ---

    # Acne (Exponential saturation curve for resolution/bounding-box invariance)
    if total_skin_pixels > 0:
        density = acne_count / (total_skin_pixels / 100000.0)
        raw_scores["acne"] = int(100 * (1.0 - np.exp(-0.03 * density)))

    # Under-eye contrast
    l_under_eye = []
    for name in ["left_under_eye", "right_under_eye"]:
        poly = regions[name]
        mask = extract_region_mask(img, poly)
        mean_l = cv2.mean(l_channel_raw, mask=mask)[0]
        l_under_eye.append(mean_l)
    avg_eye_l = 0.0
    diff = 0.0
    if l_under_eye and cheek_mean_l > 0:
        avg_eye_l = sum(l_under_eye) / len(l_under_eye)
        diff = cheek_mean_l - avg_eye_l
        raw_scores["under_eye_contrast"] = int(max(0, min(100, (diff / cheek_mean_l) * TUNING_CONFIG["dark_circles_multiplier"])))

    # Pigmentation
    avg_std_dev = 0
    if tone_std_devs:
        avg_std_dev = sum(tone_std_devs) / len(tone_std_devs)
        raw_scores["pigmentation"] = int(min(100, max(0, (avg_std_dev - TUNING_CONFIG["pigmentation_offset"]) * TUNING_CONFIG["pigmentation_multiplier"])))

    # Wrinkles
    edge_density = 0
    if wrinkle_assessable and wrinkle_analyzed_pixels > 0:
        edge_density = wrinkle_pixel_count / wrinkle_analyzed_pixels
        raw_scores["wrinkles"] = int(min(100, max(0, (edge_density - TUNING_CONFIG["wrinkle_density_offset"]) * TUNING_CONFIG["wrinkle_score_multiplier"])))

    # Oiliness
    t_zone_masks = [extract_region_mask(img, regions[n]) for n in ["forehead", "nose", "chin"]]
    combined_t_mask = cv2.bitwise_or(cv2.bitwise_or(t_zone_masks[0], t_zone_masks[1]), t_zone_masks[2])
    hsv_h, hsv_s, hsv_v = cv2.split(img_hsv)
    shine_pixels = cv2.bitwise_and(
        cv2.compare(hsv_v, TUNING_CONFIG["oiliness_v_threshold"], cv2.CMP_GT),
        cv2.compare(hsv_s, TUNING_CONFIG["oiliness_s_threshold"], cv2.CMP_LT)
    )
    shine_in_t_zone = cv2.bitwise_and(shine_pixels, shine_pixels, mask=combined_t_mask)
    t_zone_area = np.sum(combined_t_mask == 255)
    shine_ratio = 0
    if t_zone_area > 0:
        shine_ratio = np.sum(shine_in_t_zone > 0) / t_zone_area
        raw_scores["oiliness"] = int(min(100, shine_ratio * TUNING_CONFIG["oiliness_score_multiplier"]))

    # Dryness
    laplacian = cv2.Laplacian(img_gray, cv2.CV_64F)
    lap_var = np.var(laplacian)
    dryness_base = min(100, max(0, (lap_var - TUNING_CONFIG["dryness_base_offset"]) * TUNING_CONFIG["dryness_base_multiplier"]))
    raw_scores["dryness"] = int(max(0, dryness_base - (raw_scores["oiliness"] * TUNING_CONFIG["dryness_oiliness_reduction"])))

    # Set T-Zone Oiliness
    raw_scores["t_zone_oiliness"] = raw_scores["oiliness"]

    # Calculate Cheek Oiliness
    cheek_masks = [extract_region_mask(img, regions[n]) for n in ["left_cheek", "right_cheek"]]
    combined_cheek_mask = cv2.bitwise_or(cheek_masks[0], cheek_masks[1])
    shine_in_cheeks = cv2.bitwise_and(shine_pixels, shine_pixels, mask=combined_cheek_mask)
    cheeks_area = np.sum(combined_cheek_mask == 255)
    cheek_shine_ratio = 0
    if cheeks_area > 0:
        cheek_shine_ratio = np.sum(shine_in_cheeks > 0) / cheeks_area
    raw_scores["cheek_oiliness"] = int(min(100, cheek_shine_ratio * TUNING_CONFIG["oiliness_score_multiplier"]))

    # Calculate redness
    mean_a_cheeks, _ = cv2.meanStdDev(a_channel, mask=combined_cheek_mask)
    avg_cheek_a = mean_a_cheeks[0][0]
    raw_scores["redness"] = int(max(0, min(100, (avg_cheek_a - 130) * 6.6)))

    # Clamp
    for k in raw_scores:
        raw_scores[k] = max(0, min(100, raw_scores[k]))

    # --- 13. Build structured output ---
    scores = {k: {"score": v, "confidence": per_score_confidence[k]} for k, v in raw_scores.items()}

    quality = {
        "resolution": [w, h],
        "face_area_px": face_area_px,
        "faces_detected": faces_detected,
        "yaw_degrees": yaw_deg,
        "pitch_degrees": pitch_deg,
        "exposure": exposure_status,
        "lighting_uniformity": lighting_uniformity,
        "flash_detected": flash_detected,
        "preprocessing_applied": preprocessing_applied,
    }

    logger.info(
        f"CV Analysis: acne_count={acne_count}, total_skin_px={total_skin_pixels}, "
        f"avg_std_dev={avg_std_dev:.2f}, edge_density={edge_density:.5f}, "
        f"shine_ratio={shine_ratio:.5f}, lap_var={lap_var:.2f}, "
        f"cheek_mean_l={cheek_mean_l:.2f}, avg_eye_l={avg_eye_l:.2f}, diff_l={diff:.2f}, "
        f"yaw={yaw_deg}, pitch={pitch_deg}, exposure={exposure_status}, "
        f"lighting={lighting_uniformity}, flash={flash_detected}, faces={faces_detected}"
    )

    return scores, regions_serializable, quality, warnings
