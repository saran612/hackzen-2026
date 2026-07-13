import cv2
import json
from app.cv_analysis import analyze_skin_image
from app.recommendation import generate_routine

def main():
    print("Loading test image face_test.png...")
    with open("face_test.png", "rb") as f:
        img_bytes = f.read()

    print("Running face mesh and skin concern scoring...")
    try:
        scores, regions, quality, warnings = analyze_skin_image(img_bytes)
        print("Success! Face landmarks detected and segmented.")
        print("\nSkin Concern Scores:")
        print(json.dumps(scores, indent=2))

        print("\nRegion Landmarks Count:")
        for region, pts in regions.items():
            print(f"- {region}: {len(pts)} points")

        print("\nGenerating Routine:")
        routine = generate_routine(scores)
        for i, step in enumerate(routine, 1):
            print(f"{i}. [{step['step']}] {step['title']}: {step['description']}")
            print(f"   Ingredients: {', '.join(step['ingredients'])}")
            print(f"   Reasoning: {step['reason']}")

    except Exception as e:
        print(f"Error during CV analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
