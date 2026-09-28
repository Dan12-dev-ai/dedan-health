"""
Image Validation and Quality Assessment

Provides secure image validation, MIME type checking, file size limits,
and medical image quality assessment.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageStat
import numpy as np


# =============================================================================
# Configuration
# =============================================================================

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png", 
    "image/webp",
    "image/heic",
    "image/heif",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
MAX_DIMENSION = 4096
MIN_DIMENSION = 128

MIN_RESOLUTION_SCORE = 0.3
MIN_BRIGHTNESS_SCORE = 0.2
MAX_BLUR_SCORE = 0.8
MIN_CONTRAST_SCORE = 0.15


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ValidationResult:
    """Result of image validation."""
    is_valid: bool
    mime_type: Optional[str] = None
    file_size: int = 0
    dimensions: Tuple[int, int] = (0, 0)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


@dataclass
class QualityAssessment:
    """Image quality assessment results."""
    overall_score: float
    resolution: Dict[str, int]
    brightness_score: float
    contrast_score: float
    blur_score: float
    is_usable: bool
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)
# =============================================================================
# Image Validator
# =============================================================================

class ImageValidator:
    """
    Validates uploaded images for medical use.
    
    Checks:
    - MIME type
    - File size
    - Dimensions
    - Format validity
    - Malicious content (basic)
    """
    
    def __init__(
        self,
        allowed_mime_types: Optional[set] = None,
        max_file_size: int = MAX_FILE_SIZE,
        max_dimension: int = MAX_DIMENSION,
        min_dimension: int = MIN_DIMENSION,
    ):
        self.allowed_mime_types = allowed_mime_types or ALLOWED_MIME_TYPES
        self.max_file_size = max_file_size
        self.max_dimension = max_dimension
        self.min_dimension = min_dimension
    
    def validate_file(self, file_content: bytes, filename: str = "") -> ValidationResult:
        """
        Validate image file from bytes.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename (for extension check)
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(is_valid=True)
        result.file_size = len(file_content)
        
        if result.file_size == 0:
            result.errors.append("File is empty")
            result.is_valid = False
            return result
        
        if result.file_size > self.max_file_size:
            result.errors.append(
                f"File size {result.file_size / 1024 / 1024:.1f}MB exceeds "
                f"maximum {self.max_file_size / 1024 / 1024:.1f}MB"
            )
            result.is_valid = False
        
        mime_type = self._detect_mime_type(file_content)
        result.mime_type = mime_type
        
        if mime_type not in self.allowed_mime_types:
            result.errors.append(
                f"MIME type '{mime_type}' not allowed. "
                f"Allowed: {', '.join(self.allowed_mime_types)}"
            )
            result.is_valid = False
        
        if filename:
            ext = self._get_extension(filename)
            if ext not in ALLOWED_EXTENSIONS:
                result.warnings.append(
                    f"Extension '{ext}' not in allowed list: {', '.join(ALLOWED_EXTENSIONS)}"
                )
        
        try:
            image = Image.open(io.BytesIO(file_content))
            image.verify()
            image = Image.open(io.BytesIO(file_content))
            width, height = image.size
            result.dimensions = (width, height)
            
            if width < self.min_dimension or height < self.min_dimension:
                result.errors.append(
                    f"Image dimensions {width}x{height} below minimum "
                    f"{self.min_dimension}x{self.min_dimension}"
                )
                result.is_valid = False
            
            if width > self.max_dimension or height > self.max_dimension:
                result.warnings.append(
                    f"Image dimensions {width}x{height} exceed recommended "
                    f"maximum {self.max_dimension}x{self.max_dimension}. "
                    f"Will be resized for processing."
                )
            
            self._check_suspicious_content(image, result)
            
        except Exception as e:
            result.errors.append(f"Invalid image file: {str(e)}")
            result.is_valid = False
        
        return result
    
    def _detect_mime_type(self, content: bytes) -> str:
        """Detect MIME type from file signature (magic bytes)."""
        if content.startswith(b'\xff\xd8\xff'):
            return "image/jpeg"
        if content.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        if content.startswith(b'RIFF') and content[8:12] == b'WEBP':
            return "image/webp"
        if b'ftypheic' in content[:100] or b'ftypheif' in content[:100]:
            return "image/heic"
        if content.startswith(b'II\x2a\x00') or content.startswith(b'MM\x00\x2a'):
            return "image/tiff"
        return "application/octet-stream"
    
    def _get_extension(self, filename: str) -> str:
        """Get lowercase file extension."""
        return "." + filename.lower().split(".")[-1] if "." in filename else ""
    
    def _check_suspicious_content(self, image: Image.Image, result: ValidationResult):
        """Basic checks for suspicious image content."""
        if hasattr(image, 'info'):
            for key, value in image.info.items():
                if isinstance(value, str) and ('<script' in value.lower() or 'javascript:' in value.lower()):
                    result.warnings.append(f"Suspicious metadata in {key}")
        if hasattr(image, 'n_frames') and image.n_frames > 100:
            result.warnings.append(f"Image has {image.n_frames} frames (possible animation/ZIP bomb)")

# =============================================================================
# Image Quality Assessor
# =============================================================================

class ImageQualityAssessor:
    """
    Assesses medical image quality for diagnostic relevance.
    
    Evaluates:
    - Resolution adequacy
    - Brightness/exposure
    - Contrast
    - Blur/sharpness
    - Color balance
    """
    
    def __init__(
        self,
        min_resolution_score: float = MIN_RESOLUTION_SCORE,
        min_brightness_score: float = MIN_BRIGHTNESS_SCORE,
        max_blur_score: float = MAX_BLUR_SCORE,
        min_contrast_score: float = MIN_CONTRAST_SCORE,
    ):
        self.min_resolution_score = min_resolution_score
        self.min_brightness_score = min_brightness_score
        self.max_blur_score = max_blur_score
        self.min_contrast_score = min_contrast_score
    
    def assess(self, image_content: bytes) -> QualityAssessment:
        """
        Assess image quality from bytes.
        
        Args:
            image_content: Raw image bytes
            
        Returns:
            QualityAssessment with detailed scores
        """
        image = Image.open(io.BytesIO(image_content))
        
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        width, height = image.size
        
        resolution_score = self._calculate_resolution_score(width, height)
        brightness_score = self._calculate_brightness_score(image)
        contrast_score = self._calculate_contrast_score(image)
        blur_score = self._calculate_blur_score(image)
        
        overall_score = (
            resolution_score * 0.3 +
            brightness_score * 0.2 +
            contrast_score * 0.2 +
            (1.0 - blur_score) * 0.3
        )
        
        is_usable = (
            resolution_score >= self.min_resolution_score and
            brightness_score >= self.min_brightness_score and
            contrast_score >= self.min_contrast_score and
            blur_score <= self.max_blur_score
        )
        
        issues = []
        recommendations = []
        
        if resolution_score < self.min_resolution_score:
            issues.append("Low resolution - details may not be visible")
            recommendations.append("Use higher resolution camera or move closer")
        
        if brightness_score < self.min_brightness_score:
            issues.append("Image too dark")
            recommendations.append("Improve lighting or use flash")
        elif brightness_score > 0.9:
            issues.append("Image overexposed")
            recommendations.append("Reduce lighting or avoid direct flash")
        
        if contrast_score < self.min_contrast_score:
            issues.append("Low contrast - details hard to distinguish")
            recommendations.append("Improve lighting contrast or adjust camera settings")
        
        if blur_score > self.max_blur_score:
            issues.append("Image blurry - details not sharp")
            recommendations.append("Hold camera steady, ensure focus, clean lens")
        
        return QualityAssessment(
            overall_score=overall_score,
            resolution={"width": width, "height": height},
            brightness_score=brightness_score,
            contrast_score=contrast_score,
            blur_score=blur_score,
            is_usable=is_usable,
            issues=issues,
            recommendations=recommendations,
            metadata={
                "mode": image.mode,
                "format": image.format,
            }
        )
    
    def _calculate_resolution_score(self, width: int, height: int) -> float:
        min_dim = min(width, height)
        if min_dim >= 1024:
            return 1.0
        elif min_dim >= 512:
            return 0.8
        elif min_dim >= 256:
            return 0.5
        else:
            return min_dim / 512 * 0.5
    
    def _calculate_brightness_score(self, image: Image.Image) -> float:
        stat = ImageStat.Stat(image)
        mean_brightness = sum(stat.mean) / len(stat.mean) / 255.0
        
        if 0.3 <= mean_brightness <= 0.7:
            return 1.0
        elif 0.2 <= mean_brightness <= 0.8:
            return 0.7
        elif 0.1 <= mean_brightness <= 0.9:
            return 0.4
        else:
            return 0.1
    
    def _calculate_contrast_score(self, image: Image.Image) -> float:
        stat = ImageStat.Stat(image)
        std_dev = sum(stat.stddev) / len(stat.stddev) / 255.0
        
        if std_dev >= 0.25:
            return 1.0
        elif std_dev >= 0.15:
            return 0.8
        elif std_dev >= 0.10:
            return 0.5
        else:
            return std_dev / 0.15 * 0.5
    
    def _calculate_blur_score(self, image: Image.Image) -> float:
        gray = image.convert('L')
        gray_array = np.array(gray)
        
        laplacian = np.abs(
            np.roll(gray_array, 1, axis=0) +
            np.roll(gray_array, -1, axis=0) +
            np.roll(gray_array, 1, axis=1) +
            np.roll(gray_array, -1, axis=1) -
            4 * gray_array
        )
        
        variance = np.var(laplacian)
        
        if variance > 500:
            return 0.1
        elif variance > 100:
            return 0.3
        elif variance > 50:
            return 0.5
        elif variance > 20:
            return 0.7
        else:
            return 0.9

# =============================================================================
# Combined Validation Pipeline
# =============================================================================

class ImageValidationPipeline:
    """
    Complete image validation and quality assessment pipeline.
    """
    
    def __init__(
        self,
        validator: Optional[ImageValidator] = None,
        assessor: Optional[ImageQualityAssessor] = None,
    ):
        self.validator = validator or ImageValidator()
        self.assessor = assessor or ImageQualityAssessor()
    
    def process(self, file_content: bytes, filename: str = "") -> Tuple[ValidationResult, Optional[QualityAssessment]]:
        """
        Run complete validation and quality assessment.
        
        Returns:
            Tuple of (ValidationResult, QualityAssessment or None)
        """
        validation = self.validator.validate_file(file_content, filename)
        
        if not validation.is_valid:
            return validation, None
        
        quality = self.assessor.assess(file_content)
        
        return validation, quality
    
    def compute_hash(self, file_content: bytes) -> str:
        """Compute SHA-256 hash for deduplication."""
        return hashlib.sha256(file_content).hexdigest()
