def generate_routine(scores: dict) -> list:
    """
    Generates a personalized, gender-neutral skincare routine based on concern scores
    and inferred skin type.
    Accepts scores in structured format: {"concern": {"score": X, "confidence": Y}}
    or flat format: {"concern": X} for backward compatibility.
    """
    # Helper to extract numeric score from either format
    def get_score(key):
        val = scores.get(key, 0)
        if isinstance(val, dict):
            s = val.get("score", 0)
        else:
            s = val
        if s is None or isinstance(s, str):
            return 0
        return s

    # Extract all necessary scores
    acne_score = get_score("acne")
    oiliness_score = get_score("oiliness")
    dryness_score = get_score("dryness")
    wrinkles_score = get_score("wrinkles")
    pigmentation_score = get_score("pigmentation")
    dark_circles_score = max(get_score("dark_circles"), get_score("under_eye_contrast"))
    redness_score = get_score("redness")
    t_zone_oiliness = get_score("t_zone_oiliness")
    cheek_oiliness = get_score("cheek_oiliness")

    # If t_zone_oiliness or cheek_oiliness aren't provided, use overall oiliness as fallback
    if t_zone_oiliness == 0 and cheek_oiliness == 0:
        t_zone_oiliness = oiliness_score
        cheek_oiliness = oiliness_score

    # --- Layer 1: Derive Skin Type ---
    if t_zone_oiliness - cheek_oiliness > 15 and t_zone_oiliness > 40:
        skin_type = "Combination"
        skin_type_reason = f"T-zone oiliness ({t_zone_oiliness}) is significantly higher than cheeks ({cheek_oiliness}), indicating mixed zones."
    elif oiliness_score > 50 and dryness_score < 40:
        skin_type = "Oily"
        skin_type_reason = f"High overall shine score ({oiliness_score}) and low roughness ({dryness_score}) indicate sebum overproduction."
    elif dryness_score > 50 and oiliness_score < 35:
        skin_type = "Dry"
        skin_type_reason = f"Elevated roughness/texture score ({dryness_score}) and low oil levels ({oiliness_score}) indicate a dry barrier."
    elif redness_score > 40 and acne_score < 40:
        skin_type = "Sensitive-leaning"
        skin_type_reason = f"Notable diffuse redness ({redness_score}) detected without matching localized breakout clusters."
    else:
        skin_type = "Normal/Balanced"
        skin_type_reason = f"All measured hydration, oil, and sensitivity indicators are within balanced ranges."

    routine = []

    # --- Layer 2: Cleanse Step ---
    cleanser = {
        "step": "Cleanse",
        "title": "",
        "ingredients": [],
        "description": "",
        "reason": f"Formulated for {skin_type} skin: {skin_type_reason}"
    }

    if skin_type == "Oily":
        cleanser["title"] = "Purifying Gel Cleanser"
        cleanser["ingredients"] = ["Salicylic Acid (BHA)", "Zinc PCA"]
        cleanser["description"] = "A foaming gel cleanser to clear excess oil and deep clean pores without over-stripping."
    elif skin_type == "Dry":
        cleanser["title"] = "Hydrating Cream Cleanser"
        cleanser["ingredients"] = ["Ceramides", "Hyaluronic Acid"]
        cleanser["description"] = "A non-foaming, barrier-supportive cream cleanser that cleanses while restoring skin lipids."
    elif skin_type == "Combination":
        cleanser["title"] = "Balancing Foaming Cleanser"
        cleanser["ingredients"] = ["Glycerin", "Zinc PCA"]
        cleanser["description"] = "A gentle foaming cleanser that clears the oily T-zone while remaining mild on cheeks."
    elif skin_type == "Sensitive-leaning":
        cleanser["title"] = "Ultra-Gentle Calming Cleanser"
        cleanser["ingredients"] = ["Colloidal Oatmeal", "Centella Asiatica (Cica)"]
        cleanser["description"] = "A milky, non-foaming cleanser designed to calm irritation and minimize vascular flushing."
    else: # Normal/Balanced
        cleanser["title"] = "Gentle pH-Balanced Cleanser"
        cleanser["ingredients"] = ["Glycerin", "Allantoin"]
        cleanser["description"] = "A mild, everyday cleanser suitable for maintaining balanced, healthy skin."

    routine.append(cleanser)

    # --- Layer 2: Treat Step(s) ---
    # Define possible active treatments based on severity
    possible_treatments = []

    # 1. Acne Treatment
    if acne_score >= 60:
        possible_treatments.append({
            "concern": "Acne",
            "priority": 1,
            "step": "Treat (Day/Night)",
            "title": "Clinical Blemish Control Serum",
            "ingredients": ["Salicylic Acid 2%", "Niacinamide 4%"],
            "description": "High-strength formula to reduce sebum, clear comedones, and accelerate spot healing.",
            "reason": f"High acne severity score ({acne_score}) detected."
        })
    elif acne_score >= 25:
        possible_treatments.append({
            "concern": "Acne",
            "priority": 1,
            "step": "Treat (Night)",
            "title": "Targeted Blemish Spot Treatment",
            "ingredients": ["Salicylic Acid 2%"],
            "description": "Apply directly to active breakouts to calm inflammation and unclog localized pores.",
            "reason": f"Moderate acne score ({acne_score}) detected."
        })

    # 2. Wrinkle Treatment
    if wrinkles_score >= 60:
        possible_treatments.append({
            "concern": "Wrinkles",
            "priority": 2,
            "step": "Treat (Night)",
            "title": "Advanced Retinol & Peptide Complex",
            "ingredients": ["Retinol 0.5%", "Copper Peptides"],
            "description": "Powerful night treatment to accelerate cell turnover and boost dermal structural integrity. Sunscreen is non-negotiable.",
            "reason": f"High fine-lines/wrinkles score ({wrinkles_score}) detected."
        })
    elif wrinkles_score >= 25:
        possible_treatments.append({
            "concern": "Wrinkles",
            "priority": 2,
            "step": "Treat (Night)",
            "title": "Multi-Peptide Youth Serum",
            "ingredients": ["Matrixyl 3000", "Hyaluronic Acid"],
            "description": "Firming peptides that target fine lines and improve resilience without the irritation of retinoids.",
            "reason": f"Moderate wrinkle/fine-lines score ({wrinkles_score}) detected."
        })

    # 3. Pigmentation Treatment
    if pigmentation_score >= 60:
        possible_treatments.append({
            "concern": "Pigmentation",
            "priority": 3,
            "step": "Treat (Morning)",
            "title": "Pigment Corrector Serum",
            "ingredients": ["Vitamin C (L-Ascorbic) 15%", "Niacinamide 5%"],
            "description": "High-potency serum that inhibits melanin transfer and brightens dark patches. Follow with SPF.",
            "reason": f"High hyperpigmentation / uneven tone score ({pigmentation_score}) detected."
        })
    elif pigmentation_score >= 25:
        possible_treatments.append({
            "concern": "Pigmentation",
            "priority": 3,
            "step": "Treat (Morning)",
            "title": "Daily Vitamin C Brightening Serum",
            "ingredients": ["Vitamin C (Ascorbyl Glucoside)", "Alpha Arbutin"],
            "description": "Gentle daily antioxidant serum to neutralize free radicals and fade surface discoloration.",
            "reason": f"Moderate pigmentation score ({pigmentation_score}) detected."
        })

    # 4. Dark Circles Treatment
    if dark_circles_score >= 60:
        possible_treatments.append({
            "concern": "Dark Circles",
            "priority": 4,
            "step": "Eye Care",
            "title": "Vascular Support Eye Cream",
            "ingredients": ["Vitamin K", "Caffeine", "Peptides"],
            "description": "Targeted under-eye formula to improve micro-circulation, constrict leaky capillaries, and support skin thickness.",
            "reason": f"High under-eye contrast score ({dark_circles_score}) detected (likely vascular pigmentation or thin skin)."
        })
    elif dark_circles_score >= 25:
        possible_treatments.append({
            "concern": "Dark Circles",
            "priority": 4,
            "step": "Eye Care",
            "title": "Revitalizing Caffeine Eye Gel",
            "ingredients": ["Caffeine", "Hyaluronic Acid"],
            "description": "A light gel to de-puff the under-eye area and instantly brighten tired eyes.",
            "reason": f"Moderate under-eye contrast score ({dark_circles_score}) detected (likely temporary fatigue)."
        })

    # Sort treatments by priority and keep top 2
    possible_treatments.sort(key=lambda x: x["priority"])
    selected_treatments = possible_treatments[:2]
    deferred_treatments = possible_treatments[2:]

    # Add selected treatments to the routine
    for treatment in selected_treatments:
        treatment_step = {
            "step": treatment["step"],
            "title": treatment["title"],
            "ingredients": treatment["ingredients"],
            "description": treatment["description"],
            "reason": treatment["reason"]
        }
        
        # Add a note if other treatments were deprioritized
        if deferred_treatments:
            deferred_names = [t["concern"] for t in deferred_treatments]
            treatment_step["reason"] += f" (Note: deferred treatment for {', '.join(deferred_names)} to prevent skin barrier overload)."
            
        routine.append(treatment_step)

    # --- Layer 2: Hydrate Step ---
    moisturizer = {
        "step": "Hydrate",
        "title": "",
        "ingredients": [],
        "description": "",
        "reason": f"Hydration texture selected for {skin_type} skin."
    }

    if skin_type == "Oily":
        moisturizer["title"] = "Oil-Free Hydrating Gel"
        moisturizer["ingredients"] = ["Hyaluronic Acid", "Niacinamide"]
        moisturizer["description"] = "A feather-light water gel that offers deep hydration with a shine-free, matte finish."
    elif skin_type == "Dry":
        moisturizer["title"] = "Rich Ceramides Barrier Cream"
        moisturizer["ingredients"] = ["Ceramides AP/EOP/NP", "Shea Butter", "Squalane"]
        moisturizer["description"] = "A rich, lipid-dense cream to repair flaky skin patches and prevent trans-epidermal water loss."
    elif skin_type == "Combination":
        moisturizer["title"] = "Lightweight Balancing Gel-Cream"
        moisturizer["ingredients"] = ["Squalane", "Hyaluronic Acid", "Centella Asiatica"]
        moisturizer["description"] = "A hybrid gel-cream that hydrates drier cheeks while absorbing excess shine in the T-zone."
    elif skin_type == "Sensitive-leaning":
        moisturizer["title"] = "Soothing Cica Barrier Cream"
        moisturizer["ingredients"] = ["Ceramides", "Centella Asiatica (Cica)", "Allantoin"]
        moisturizer["description"] = "A minimalist, fragrance-free cream that forms a protective, non-irritating layer over compromised skin."
    else: # Normal/Balanced
        moisturizer["title"] = "Barrier Support Moisturizer"
        moisturizer["ingredients"] = ["Ceramides", "Squalane"]
        moisturizer["description"] = "A balanced daily moisturizer that maintains a healthy skin barrier and a smooth complexion."

    routine.append(moisturizer)

    # --- Layer 2: Protect Step ---
    sunscreen = {
        "step": "Protect (Morning)",
        "title": "",
        "ingredients": [],
        "description": "",
        "reason": f"UV protection tailored for {skin_type} skin."
    }

    # Sunscreen rule (emphasize sunscreen if wrinkles/pigmentation or retinol is high severity)
    sunscreen_critical = wrinkles_score >= 60 or pigmentation_score >= 60
    emphasis_note = " Crucial to protect skin and prevent worsening of active concerns." if sunscreen_critical else ""

    if skin_type == "Oily" or skin_type == "Combination":
        sunscreen["title"] = "Oil-Control Matte Sunscreen SPF 50+"
        sunscreen["ingredients"] = ["Zinc Oxide", "Niacinamide"]
        sunscreen["description"] = "Broad-spectrum physical sunscreen that absorbs excess sebum and leaves a velvety matte feel." + emphasis_note
    elif skin_type == "Dry":
        sunscreen["title"] = "Hydrating Fluid Sunscreen SPF 50+"
        sunscreen["ingredients"] = ["Hyaluronic Acid", "Organic UV Filters"]
        sunscreen["description"] = "A nourishing, dewy-finish sunscreen that keeps skin plump and hydrated all day." + emphasis_note
    elif skin_type == "Sensitive-leaning":
        sunscreen["title"] = "Mineral Calming Sunscreen SPF 50+"
        sunscreen["ingredients"] = ["Zinc Oxide", "Titanium Dioxide", "Bisabolol"]
        sunscreen["description"] = "A 100% mineral sunscreen formulated without potential allergens or synthetic dyes." + emphasis_note
    else: # Normal/Balanced
        sunscreen["title"] = "Daily Light Fluid SPF 50+"
        sunscreen["ingredients"] = ["Zinc Oxide", "Vitamin E"]
        sunscreen["description"] = "A lightweight daily fluid that blends seamlessly on all skin tones with zero white cast." + emphasis_note

    routine.append(sunscreen)

    return routine
