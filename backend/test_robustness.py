"""
SkinCV Robustness Regression Tests
===================================
Quick sanity-bound tests to verify the CV pipeline handles edge cases
gracefully without crashes or unhandled exceptions.

Run: ./venv/bin/python test_robustness.py
"""

import sys
import os
import numpy as np
import cv2

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.cv_analysis import analyze_skin_image
from app.recommendation import generate_routine
from fastapi import HTTPException

PASS = 0
FAIL = 0


def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  [PASS] {name}")
        PASS += 1
    except AssertionError as e:
        print(f"  [FAIL] {name}: {e}")
        FAIL += 1
    except Exception as e:
        print(f"  [FAIL] {name}: Unexpected error: {type(e).__name__}: {e}")
        FAIL += 1


# ---------------------------------------------------------------------------
# Test 1: Solid black image → should reject with "No face detected"
# ---------------------------------------------------------------------------
def test_black_image():
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    image_bytes = buf.tobytes()
    try:
        analyze_skin_image(image_bytes)
        assert False, "Should have raised HTTPException for no face"
    except HTTPException as e:
        assert e.status_code == 400
        assert "No face detected" in e.detail


# ---------------------------------------------------------------------------
# Test 2: Random noise image → should reject with "No face detected"
# ---------------------------------------------------------------------------
def test_noise_image():
    rng = np.random.RandomState(42)
    img = rng.randint(0, 256, (400, 400, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    image_bytes = buf.tobytes()
    try:
        analyze_skin_image(image_bytes)
        assert False, "Should have raised HTTPException for no face"
    except HTTPException as e:
        assert e.status_code == 400
        assert "No face detected" in e.detail


# ---------------------------------------------------------------------------
# Test 3: Very small image (50x50) → should reject with resolution error
# ---------------------------------------------------------------------------
def test_small_image():
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    image_bytes = buf.tobytes()
    try:
        analyze_skin_image(image_bytes)
        assert False, "Should have raised HTTPException for low resolution"
    except HTTPException as e:
        assert e.status_code == 400
        assert "resolution" in e.detail.lower()


# ---------------------------------------------------------------------------
# Test 4: Invalid bytes → should reject with decode error
# ---------------------------------------------------------------------------
def test_invalid_bytes():
    image_bytes = b"this is not an image at all"
    try:
        analyze_skin_image(image_bytes)
        assert False, "Should have raised HTTPException for invalid format"
    except HTTPException as e:
        assert e.status_code == 400
        assert "Invalid" in e.detail or "invalid" in e.detail.lower()


# ---------------------------------------------------------------------------
# Test 5: Valid portrait → should return scores with confidence
# ---------------------------------------------------------------------------
def test_valid_portrait():
    test_path = os.path.join(os.path.dirname(__file__), "face_test.png")
    if not os.path.exists(test_path):
        # Skip if no test image available
        print(f"    (skipping: {test_path} not found)")
        return

    with open(test_path, "rb") as f:
        image_bytes = f.read()

    scores, regions, quality, warnings = analyze_skin_image(image_bytes)

    # Verify structured scores
    assert isinstance(scores, dict), "scores should be a dict"
    for key, val in scores.items():
        assert isinstance(val, dict), f"scores[{key}] should be a dict with score/confidence"
        assert "score" in val, f"scores[{key}] missing 'score'"
        assert "confidence" in val, f"scores[{key}] missing 'confidence'"
        assert 0 <= val["score"] <= 100, f"scores[{key}]['score'] out of range: {val['score']}"
        assert val["confidence"] in ("high", "medium", "low"), f"Invalid confidence: {val['confidence']}"

    # Verify quality metadata
    assert isinstance(quality, dict), "quality should be a dict"
    assert "resolution" in quality
    assert "faces_detected" in quality
    assert quality["faces_detected"] >= 1
    assert "yaw_degrees" in quality
    assert "exposure" in quality
    assert "flash_detected" in quality

    # Verify regions
    assert isinstance(regions, dict), "regions should be a dict"
    assert "forehead" in regions
    assert "left_cheek" in regions

    # Verify warnings is a list
    assert isinstance(warnings, list), "warnings should be a list"

    # Verify recommendation engine handles structured scores
    routine = generate_routine(scores)
    assert isinstance(routine, list) and len(routine) >= 3, "routine should have at least 3 steps"


# ---------------------------------------------------------------------------
# Test 6: Solid white image → should reject (no face, tests overexposure path)
# ---------------------------------------------------------------------------
def test_white_image():
    img = np.full((400, 400, 3), 255, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    image_bytes = buf.tobytes()
    try:
        analyze_skin_image(image_bytes)
        assert False, "Should have raised HTTPException for no face"
    except HTTPException as e:
        assert e.status_code == 400


# ---------------------------------------------------------------------------
# Test 7: Recommendation engine backward compatibility (flat scores)
# ---------------------------------------------------------------------------
def test_recommendation_flat_scores():
    flat_scores = {"acne": 50, "dark_circles": 40, "pigmentation": 60,
                   "oiliness": 30, "dryness": 10, "wrinkles": 20,
                   "under_eye_contrast": 0}
    routine = generate_routine(flat_scores)
    assert isinstance(routine, list)
    assert len(routine) >= 3


# ===========================================================================
if __name__ == "__main__":
    print("\n=== SkinCV Robustness Regression Tests ===\n")

    test("Black image → No face detected", test_black_image)
    test("Noise image → No face detected", test_noise_image)
    test("Small image (50x50) → Resolution error", test_small_image)
    test("Invalid bytes → Decode error", test_invalid_bytes)
    test("White image → No face detected", test_white_image)
    test("Recommendation flat scores → Backward compat", test_recommendation_flat_scores)
    test("Valid portrait → Structured output with confidence", test_valid_portrait)

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===\n")
    sys.exit(1 if FAIL > 0 else 0)
