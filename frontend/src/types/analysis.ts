export interface MetadataResult {
  has_exif: boolean;
  camera_make: string | null;
  camera_model: string | null;
  software: string | null;
  gps_present: boolean;
  original_date: string | null;
  has_thumbnail: boolean;
  suspicious_signals: string[];
  risk_score: number;
}

export interface ReverseImageMatch {
  source_url: string;
  page_title: string;
  thumbnail_url: string | null;
  is_stock_site: boolean;
}

export interface ReverseImageResult {
  total_matches: number;
  matches: ReverseImageMatch[];
  found_on_stock_sites: boolean;
  found_on_social_media: boolean;
  suspicious_signals: string[];
  risk_score: number;
}

export interface FaceAnalysisResult {
  faces_detected: number;
  dominant_emotion: string | null;
  estimated_age: number | null;
  gender: string | null;
  is_high_quality: boolean;
  face_confidence: number | null;
  suspicious_signals: string[];
  risk_score: number;
}

export interface CatfishResult {
  overall_score: number;
  verdict: string;
  metadata: MetadataResult;
  reverse_image: ReverseImageResult;
  face_analysis: FaceAnalysisResult;
  analysis_duration_ms: number;
}
