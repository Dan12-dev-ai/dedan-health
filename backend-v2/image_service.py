"""
Image Service — DEDAN Health

Handles secure image upload, validation, and temporary storage.
"""

import os
import uuid
import hashlib
import base64
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import logging

from PIL import Image
import io

# Import schemas directly
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.schemas import ImageUploadResponse

logger = logging.getLogger(__name__)


class ImageValidationError(Exception):
    def __init__(self, message: str, errors: List[str] = None, warnings: List[str] = None):
        self.message = message
        self.errors = errors or []
        self.warnings = warnings or []
        super().__init__(message)


class ImageQualityAssessment:
    def __init__(self):
        self.min_dimension = 224
        self.max_dimension = 4096
        self.min_file_size = 1024
        self.max_file_size = 10 * 1024 * 1024

    def assess(self, image: Image.Image, file_size: int) -> Dict[str, Any]:
        width, height = image.size
        aspect_ratio = width / height if height > 0 else 0
        
        issues = []
        warnings = []
        
        if width < self.min_dimension or height < self.min_dimension:
            issues.append(f"Image too small: {width}x{height} (minimum {self.min_dimension}x{self.min_dimension})")
        if width > self.max_dimension or height > self.max_dimension:
            warnings.append(f"Image very large: {width}x{height} (will be downsampled)")
        
        if aspect_ratio < 0.3 or aspect_ratio > 3.5:
            warnings.append(f"Unusual aspect ratio: {aspect_ratio:.2f} - may affect analysis")
        
        if file_size < self.min_file_size:
            issues.append(f"File too small: {file_size} bytes (may be corrupted)")
        if file_size > self.max_file_size:
            issues.append(f"File too large: {file_size/1024/1024:.1f}MB (max 10MB)")
        
        if image.mode not in ("RGB", "RGBA", "L"):
            warnings.append(f"Image mode {image.mode} converted to RGB")
        
        score = 1.0
        if issues:
            score -= 0.3 * len(issues)
        if warnings:
            score -= 0.1 * len(warnings)
        score = max(0.0, min(1.0, score))
        
        is_usable = len(issues) == 0 and score >= 0.3
        
        return {
            "resolution": f"{width}x{height}",
            "aspect_ratio": round(aspect_ratio, 2),
            "mode": image.mode,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "overall_score": round(score, 2),
            "is_usable": is_usable,
            "issues": issues,
            "warnings": warnings,
        }


class ImageService:
    def __init__(self, settings=None):
        from app.core.config import get_settings
        self.settings = settings or get_settings()
        self.storage_path = Path(self.settings.IMAGE_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.quality_assessor = ImageQualityAssessment()
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def validate_and_store(
        self,
        file_content: bytes,
        filename: str,
        session_id: Optional[str] = None,
    ) -> ImageUploadResponse:
        mime_type = self._get_mime_type(file_content, filename)
        if mime_type not in self.settings.ALLOWED_IMAGE_TYPES:
            raise ImageValidationError(
                f"Unsupported file type: {mime_type}",
                errors=[f"Allowed types: {', '.join(self.settings.ALLOWED_IMAGE_TYPES)}"]
            )

        file_size = len(file_content)
        max_size = self.settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise ImageValidationError(
                f"File too large: {file_size/1024/1024:.1f}MB (max {self.settings.MAX_IMAGE_SIZE_MB}MB)",
                errors=["File exceeds maximum size limit"]
            )

        try:
            image = Image.open(io.BytesIO(file_content))
            image.verify()
            image = Image.open(io.BytesIO(file_content))
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
        except Exception as e:
            raise ImageValidationError("Invalid or corrupted image file", errors=[str(e)])

        quality = self.quality_assessor.assess(image, file_size)
        if not quality["is_usable"]:
            raise ImageValidationError("Image quality insufficient for medical analysis", errors=quality["issues"], warnings=quality["warnings"])

        image_id = str(uuid.uuid4())
        content_hash = hashlib.sha256(file_content).hexdigest()
        safe_filename = self._sanitize_filename(filename)
        ext = Path(safe_filename).suffix or ".jpg"
        stored_filename = f"{image_id}{ext}"
        file_path = self.storage_path / stored_filename
        
        image.save(file_path, quality=90, optimize=True)
        actual_size = file_path.stat().st_size

        metadata = {
            "image_id": image_id,
            "original_filename": filename,
            "stored_filename": stored_filename,
            "content_hash": content_hash,
            "mime_type": mime_type,
            "size": actual_size,
            "dimensions": f"{image.width}x{image.height}",
            "quality": quality,
            "session_id": session_id,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=self.settings.IMAGE_TTL_HOURS)).isoformat(),
        }
        self._metadata[image_id] = metadata

        logger.info(f"Image uploaded: {image_id} ({actual_size} bytes, {image.width}x{image.height})")

        return ImageUploadResponse(
            image_id=image_id,
            filename=filename,
            size_bytes=actual_size,
            mime_type=mime_type,
            quality_score=quality["overall_score"],
            is_usable=quality["is_usable"],
            upload_timestamp=datetime.fromisoformat(metadata["upload_timestamp"]),
            preview_url=f"/api/images/{image_id}/preview",
        )

    def validate_and_store_base64(
        self,
        base64_data: str,
        filename: str = "image.jpg",
        session_id: Optional[str] = None,
    ) -> ImageUploadResponse:
        if base64_data.startswith("data:"):
            try:
                header, base64_data = base64_data.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
                ext = mimetypes.guess_extension(mime_type) or ".jpg"
                filename = f"image{ext}"
            except Exception:
                pass

        try:
            file_content = base64.b64decode(base64_data)
        except Exception as e:
            raise ImageValidationError("Invalid base64 encoding", errors=[str(e)])

        return self.validate_and_store(file_content, filename, session_id)

    def get_image(self, image_id: str) -> Optional[bytes]:
        metadata = self._metadata.get(image_id)
        if not metadata:
            return None
        file_path = self.storage_path / metadata["stored_filename"]
        if not file_path.exists():
            return None
        with open(file_path, "rb") as f:
            return f.read()

    def get_image_base64(self, image_id: str) -> Optional[str]:
        content = self.get_image(image_id)
        if content is None:
            return None
        return base64.b64encode(content).decode()

    def get_metadata(self, image_id: str) -> Optional[Dict[str, Any]]:
        return self._metadata.get(image_id)

    def delete_image(self, image_id: str) -> bool:
        metadata = self._metadata.pop(image_id, None)
        if not metadata:
            return False
        file_path = self.storage_path / metadata["stored_filename"]
        if file_path.exists():
            file_path.unlink()
        logger.info(f"Image deleted: {image_id}")
        return True

    def cleanup_expired(self) -> int:
        now = datetime.utcnow()
        deleted = 0
        expired_ids = [
            img_id for img_id, meta in self._metadata.items()
            if datetime.fromisoformat(meta["expires_at"]) < now
        ]
        for img_id in expired_ids:
            self.delete_image(img_id)
            deleted += 1
        if deleted:
            logger.info(f"Cleaned up {deleted} expired images")
        return deleted

    def _get_mime_type(self, content: bytes, filename: str) -> str:
        if content.startswith(b'\xff\xd8\xff'):
            return "image/jpeg"
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        elif content.startswith(b'RIFF') and b'WEBP' in content[:12]:
            return "image/webp"
        elif content.startswith(b'\x00\x00\x00') and b'ftypheic' in content[:12]:
            return "image/heic"
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def _sanitize_filename(self, filename: str) -> str:
        filename = os.path.basename(filename)
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
        filename = "".join(c for c in filename if c in safe_chars)
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:90] + ext
        return filename or "image.jpg"


# Global instance
image_service = ImageService()
