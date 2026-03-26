WEIGHTS = {
    "metadata": 0.20,
    "reverse_image": 0.50,
    "face_analysis": 0.30,
}


def compute_overall_score(
    metadata_score: int,
    reverse_image_score: int,
    face_analysis_score: int,
) -> tuple[int, str]:
    raw = (
        metadata_score * WEIGHTS["metadata"]
        + reverse_image_score * WEIGHTS["reverse_image"]
        + face_analysis_score * WEIGHTS["face_analysis"]
    )
    score = max(0, min(100, round(raw)))

    if score < 30:
        verdict = "Likely Safe"
    elif score < 65:
        verdict = "Suspicious"
    else:
        verdict = "High Risk"

    return score, verdict
