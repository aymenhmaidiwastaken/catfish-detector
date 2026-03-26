from pydantic import BaseModel


class MetadataResult(BaseModel):
    has_exif: bool
    camera_make: str | None = None
    camera_model: str | None = None
    software: str | None = None
    gps_present: bool = False
    original_date: str | None = None
    has_thumbnail: bool = False
    suspicious_signals: list[str] = []
    risk_score: int = 0


class ReverseImageMatch(BaseModel):
    source_url: str
    page_title: str = ""
    thumbnail_url: str | None = None
    is_stock_site: bool = False


class ReverseImageResult(BaseModel):
    total_matches: int = 0
    matches: list[ReverseImageMatch] = []
    found_on_stock_sites: bool = False
    found_on_social_media: bool = False
    suspicious_signals: list[str] = []
    risk_score: int = 0


class FaceAnalysisResult(BaseModel):
    faces_detected: int = 0
    dominant_emotion: str | None = None
    estimated_age: int | None = None
    gender: str | None = None
    is_high_quality: bool = False
    face_confidence: float | None = None
    suspicious_signals: list[str] = []
    risk_score: int = 0


class CatfishResult(BaseModel):
    overall_score: int
    verdict: str
    metadata: MetadataResult
    reverse_image: ReverseImageResult
    face_analysis: FaceAnalysisResult
    analysis_duration_ms: int
