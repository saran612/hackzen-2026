def generate_routine(scores: dict) -> list:
    """
    Generates a personalized, gender-neutral skincare routine based on concern scores.
    Accepts scores in structured format: {"concern": {"score": X, "confidence": Y}}
    or flat format: {"concern": X} for backward compatibility.
    """
    # Helper to extract numeric score from either format
    def get_score(key):
        val = scores.get(key, 0)
        if isinstance(val, dict):
            return val.get("score", 0)
        return val

    routine = []

    # 1. Cleanse (Always present, formulation changes)
    cleanser = {
        "step": "Cleanse",
        "title": "Daily Cleanser",
        "ingredients": ["Glycerin", "Ceramides"],
        "description": "Wash face morning and night with lukewarm water. Pat dry with a clean towel."
    }
    if get_score("oiliness") > 50 or get_score("acne") > 30:
        cleanser["title"] = "Purifying Gel Cleanser"
        cleanser["ingredients"] = ["Salicylic Acid (BHA)", "Zinc PCA"]
        cleanser["description"] = "A foaming gel cleanser to clear excess oil and unclog pores without stripping moisture."
    elif get_score("dryness") > 50:
        cleanser["title"] = "Hydrating Cream Cleanser"
        cleanser["ingredients"] = ["Ceramides", "Hyaluronic Acid"]
        cleanser["description"] = "A non-foaming cream cleanser that maintains the skin's moisture barrier while gently removing impurities."
    else:
        cleanser["title"] = "Gentle pH-Balanced Cleanser"
        cleanser["ingredients"] = ["Glycerin", "Allantoin"]
        cleanser["description"] = "A mild, everyday cleanser suitable for maintaining balanced, healthy skin."
        
    routine.append(cleanser)

    # 2. Treat (Optional/Conditional - Serum or Spot Treatment)
    treatments = []
    
    if get_score("acne") > 30:
        treatments.append({
            "step": "Treat (Day/Night)",
            "title": "Blemish Control Spot Treatment",
            "ingredients": ["Salicylic Acid 2%", "Niacinamide"],
            "description": "Apply directly to active breakouts to reduce redness, inflammation, and accelerate skin recovery."
        })

    if get_score("pigmentation") > 30:
        treatments.append({
            "step": "Treat (Morning)",
            "title": "Brightening Serum",
            "ingredients": ["Vitamin C (L-Ascorbic Acid)", "Alpha Arbutin"],
            "description": "Apply a few drops in the morning before moisturizing to even out skin tone and fade hyperpigmentation."
        })

    if get_score("wrinkles") > 30:
        treatments.append({
            "step": "Treat (Night)",
            "title": "Renewing Retinoid Serum",
            "ingredients": ["Retinol 0.5%", "Peptides"],
            "description": "Apply in the evening on dry skin. Retinol accelerates cellular turnover to smooth fine lines and refine texture. Use sunscreen daily."
        })

    # Support both old key "dark_circles" and new "under_eye_contrast"
    dark_circle_score = max(get_score("dark_circles"), get_score("under_eye_contrast"))
    if dark_circle_score > 30:
        treatments.append({
            "step": "Eye Care",
            "title": "Revitalizing Eye Serum",
            "ingredients": ["Caffeine", "Hyaluronic Acid"],
            "description": "Gently pat a small amount around the under-eye area. Helps reduce puffiness and brighten shadows."
        })

    # Add up to 2 treatment steps for simplicity
    for t in treatments[:2]:
        routine.append(t)

    # 3. Hydrate (Always present, formulation changes)
    moisturizer = {
        "step": "Hydrate",
        "title": "Barrier Support Moisturizer",
        "ingredients": ["Ceramides", "Squalane"],
        "description": "Apply morning and night to seal in moisture and protect the skin barrier."
    }
    if get_score("oiliness") > 50:
        moisturizer["title"] = "Oil-Free Hydrating Gel"
        moisturizer["ingredients"] = ["Hyaluronic Acid", "Niacinamide"]
        moisturizer["description"] = "A lightweight water-gel moisturizer that provides deep hydration without clogging pores or feeling greasy."
    elif get_score("dryness") > 50:
        moisturizer["title"] = "Rich Barrier Cream"
        moisturizer["ingredients"] = ["Ceramides", "Shea Butter", "Squalane"]
        moisturizer["description"] = "A nourishing, thick cream to deeply moisturize, prevent moisture loss, and soothe dry patches."
        
    routine.append(moisturizer)

    # 4. Protect (Always present in morning)
    protection = {
        "step": "Protect (Morning)",
        "title": "Broad Spectrum SPF 50+",
        "ingredients": ["Zinc Oxide", "Chemical or Mineral UV Filters"],
        "description": "Apply as the final step of the morning routine. Crucial for protecting skin from premature aging, damage, and post-acne dark marks."
    }
    routine.append(protection)

    return routine
