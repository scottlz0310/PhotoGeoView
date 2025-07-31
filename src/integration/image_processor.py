"""
CS4Coding ImageProcessor with Kiro Integration

Integrates CS4Coding's high-precision EXIF parsing with Kiro optimization:
- CS4Coding: Robust EXIF data extraction and GPS coordinate processing
- Kiro: Performance monitoring, caching, and error handling

Author: Kiro AI Integration System
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config_manager import ConfigManager
from .error_handling import ErrorCategory, IntegratedErrorHandler
from .interfaces import IImageProcessor
from .logging_system import LoggerSystem
from .models import AIComponent, ImageMetadata, ProcessingStatus

# Check library availability
try:
    import exifread

    EXIFREAD_AVAILABLE = True
except ImportError:
    EXIFREAD_AVAILABLE = False

try:
    from PIL import Image, ImageOps

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class CS4CodingImageProcessor(IImageProcessor):
    """
    CS4Coding ImageProcessor with Kiro optimization

    Features:
    - CS4Coding's high-precision EXIF parsing
    - GPS coordinate extraction and validation
    - Kiro's performance monitoring and caching
    - Unified error handling and logging
    """

    def __init__(
        self, config_manager: ConfigManager = None, logger_system: LoggerSystem = None
    ):
        """
        Initialize the CS4Coding ImageProcessor

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
        """

        self.config_manager = config_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Performance tracking
        self.processing_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Cache for processed images and metadata
        self.image_cache: Dict[str, Any] = {}
        self.metadata_cache: Dict[str, ImageMetadata] = {}
        self.cache_lock = threading.RLock()

        # Supported formats (CS4Coding standard)
        self.supported_formats = [
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tiff",
            ".tif",
            ".gif",
            ".webp",
            ".raw",
            ".cr2",
            ".nef",
            ".arw",
        ]

        self.logger_system.log_ai_operation(
            AIComponent.COPILOT,
            "image_processor_init",
            "CS4Coding ImageProcessor initialized",
        )

    def load_image(self, path: Path) -> Optional[Any]:
        """
        Load an image from the specified path

        Args:
            path: Path to the image file

        Returns:
            Loaded image object or None if failed
        """

        start_time = time.time()

        try:
            # Validate file exists first
            if not path.exists():
                return None

            # Check cache first (Kiro optimization)
            cache_key = f"image_{path}_{path.stat().st_mtime}"

            with self.cache_lock:
                if cache_key in self.image_cache:
                    self.cache_hits += 1
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "image_cache_hit",
                        f"Cache hit for {path.name}",
                    )
                    return self.image_cache[cache_key]

                self.cache_misses += 1

            # Validate file
            if not self.validate_image(path):
                return None

            # Load image using available library
            image = None

            if PIL_AVAILABLE:
                image = self._load_with_pil(path)
            elif CV2_AVAILABLE:
                image = self._load_with_cv2(path)

            if image is not None:
                # Cache the loaded image (Kiro optimization)
                with self.cache_lock:
                    self.image_cache[cache_key] = image

                    # Limit cache size
                    if len(self.image_cache) > 100:
                        # Remove oldest 20 items
                        keys_to_remove = list(self.image_cache.keys())[:20]
                        for key in keys_to_remove:
                            del self.image_cache[key]

                # Track performance
                processing_time = time.time() - start_time
                self.processing_times.append(processing_time)

                # Keep only recent times
                if len(self.processing_times) > 100:
                    self.processing_times = self.processing_times[-100:]

                self.logger_system.log_performance(
                    AIComponent.COPILOT,
                    "image_load",
                    {
                        "duration": processing_time,
                        "file_size": path.stat().st_size,
                        "cache_hit": False,
                    },
                )

            return image

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "image_load", "file_path": str(path)},
                AIComponent.COPILOT,
            )
            return None

    def _load_with_pil(self, path: Path) -> Optional[Any]:
        """Load image using PIL"""

        try:
            image = Image.open(path)

            # Auto-rotate based on EXIF orientation (CS4Coding feature)
            image = ImageOps.exif_transpose(image)

            return image

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.COPILOT, e, "pil_image_load", {"file_path": str(path)}
            )
            return None

    def _load_with_cv2(self, path: Path) -> Optional[Any]:
        """Load image using OpenCV"""

        try:
            image = cv2.imread(str(path))

            if image is not None:
                # Convert BGR to RGB (OpenCV uses BGR by default)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            return image

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.COPILOT, e, "cv2_image_load", {"file_path": str(path)}
            )
            return None

    def generate_thumbnail(self, image: Any, size: Tuple[int, int]) -> Optional[Any]:
        """
        Generate a thumbnail from the given image

        Args:
            image: Source image object
            size: Desired thumbnail size (width, height)

        Returns:
            Thumbnail image object or None if failed
        """

        start_time = time.time()

        try:
            if image is None:
                return None

            thumbnail = None

            if PIL_AVAILABLE and hasattr(image, "thumbnail"):
                # PIL image
                thumbnail = image.copy()
                thumbnail.thumbnail(size, Image.Resampling.LANCZOS)

            elif CV2_AVAILABLE and hasattr(image, "shape"):
                # OpenCV image
                height, width = image.shape[:2]
                aspect_ratio = width / height

                if aspect_ratio > 1:
                    new_width = size[0]
                    new_height = int(size[0] / aspect_ratio)
                else:
                    new_height = size[1]
                    new_width = int(size[1] * aspect_ratio)

                thumbnail = cv2.resize(
                    image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4
                )

            # Track performance
            processing_time = time.time() - start_time

            self.logger_system.log_performance(
                AIComponent.COPILOT,
                "thumbnail_generation",
                {
                    "duration": processing_time,
                    "target_size": size,
                    "success": thumbnail is not None,
                },
            )

            return thumbnail

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "thumbnail_generation", "size": size},
                AIComponent.COPILOT,
            )
            return None

    def extract_exif(self, path: Path) -> Dict[str, Any]:
        """
        Extract EXIF metadata from image file (CS4Coding precision)

        Args:
            path: Path to the image file

        Returns:
            Dictionary containing EXIF data
        """

        start_time = time.time()

        try:
            # Validate file exists first
            if not path.exists():
                return {}

            # Check cache first
            cache_key = f"exif_{path}_{path.stat().st_mtime}"

            with self.cache_lock:
                if cache_key in self.metadata_cache:
                    self.cache_hits += 1
                    cached_metadata = self.metadata_cache[cache_key]
                    return self._metadata_to_dict(cached_metadata)

            self.cache_misses += 1

            # Extract EXIF data
            exif_data = {}

            # Get basic file information
            file_info = self._get_file_info(path)
            if file_info:
                exif_data.update(file_info)

            # Try ExifRead first (CS4Coding preference)
            if EXIFREAD_AVAILABLE:
                exif_data.update(self._extract_with_exifread(path))
            elif PIL_AVAILABLE:
                exif_data.update(self._extract_with_pil(path))

            # Create ImageMetadata object
            metadata = self._create_image_metadata(path, exif_data)

            # Cache the metadata
            with self.cache_lock:
                self.metadata_cache[cache_key] = metadata

                # Limit cache size
                if len(self.metadata_cache) > 200:
                    keys_to_remove = list(self.metadata_cache.keys())[:50]
                    for key in keys_to_remove:
                        del self.metadata_cache[key]

            # Track performance
            processing_time = time.time() - start_time

            self.logger_system.log_performance(
                AIComponent.COPILOT,
                "exif_extraction",
                {
                    "duration": processing_time,
                    "file_size": path.stat().st_size,
                    "has_gps": metadata.has_gps,
                    "exif_tags_count": len(exif_data),
                },
            )

            return exif_data

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "exif_extraction", "file_path": str(path)},
                AIComponent.COPILOT,
            )
            return {}

    def _extract_with_exifread(self, path: Path) -> Dict[str, Any]:
        """Extract EXIF using exifread library (CS4Coding implementation)"""

        exif_data = {}

        try:
            with open(path, "rb") as f:
                tags = exifread.process_file(f, details=False)

                if tags:
                    # Parse basic EXIF data
                    exif_data.update(self._parse_exifread_tags(tags))

                    # Extract GPS data
                    gps_data = self._extract_gps_from_exifread(tags)
                    if gps_data:
                        exif_data.update(gps_data)

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.COPILOT, e, "exifread_extraction", {"file_path": str(path)}
            )

        return exif_data

    def _parse_exifread_tags(self, tags: Dict[str, Any]) -> Dict[str, str]:
        """Parse ExifRead tags into readable format (CS4Coding implementation)"""

        parsed = {}

        # Mapping of important EXIF tags
        tag_mapping = {
            "Image Make": "Camera Make",
            "Image Model": "Camera Model",
            "Image DateTime": "Date Taken",
            "Image Orientation": "Orientation",
            "EXIF DateTimeOriginal": "Date Original",
            "EXIF ExifImageWidth": "Image Width",
            "EXIF ExifImageLength": "Image Height",
            "EXIF ISO": "ISO Speed",
            "EXIF ISOSpeedRatings": "ISO Speed",
            "EXIF FNumber": "F-Number",
            "EXIF ExposureTime": "Exposure Time",
            "EXIF FocalLength": "Focal Length",
            "EXIF FocalLengthIn35mmFilm": "Focal Length (35mm)",
            "EXIF Flash": "Flash",
            "EXIF WhiteBalance": "White Balance",
            "EXIF LensModel": "Lens Model",
            "EXIF ExposureMode": "Exposure Mode",
        }

        # Excluded tags (binary data or less important)
        excluded_tags = {
            "JPEGThumbnail",
            "TIFFThumbnail",
            "Filename",
            "EXIF MakerNote",
            "EXIF UserComment",
            "EXIF ColorSpace",
            "EXIF ComponentsConfiguration",
        }

        for tag_key, tag_value in tags.items():
            try:
                tag_str = str(tag_key)

                if tag_str in excluded_tags:
                    continue

                if tag_str in tag_mapping:
                    readable_key = tag_mapping[tag_str]
                    parsed[readable_key] = str(tag_value)
                else:
                    # Include other important tags
                    if any(
                        keyword in tag_str.lower()
                        for keyword in [
                            "image",
                            "exif",
                            "camera",
                            "lens",
                            "exposure",
                            "iso",
                            "flash",
                        ]
                    ):
                        clean_key = tag_str.replace("Image ", "").replace("EXIF ", "")
                        parsed[clean_key] = str(tag_value)

            except Exception as e:
                self.logger_system.log_error(
                    AIComponent.COPILOT,
                    e,
                    "exif_tag_parsing",
                    {"tag_key": str(tag_key)},
                )

        return parsed

    def _extract_gps_from_exifread(
        self, tags: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract GPS data from ExifRead tags (CS4Coding implementation)"""

        try:
            gps_data = {}

            # 緯度・経度の処理
            gps_tags = [
                "GPS GPSLatitude",
                "GPS GPSLatitudeRef",
                "GPS GPSLongitude",
                "GPS GPSLongitudeRef",
            ]

            if all(tag in tags for tag in gps_tags):
                lat_tag = tags["GPS GPSLatitude"]
                lat_ref_tag = tags["GPS GPSLatitudeRef"]
                lon_tag = tags["GPS GPSLongitude"]
                lon_ref_tag = tags["GPS GPSLongitudeRef"]

                # Convert to decimal degrees
                lat_decimal = self._convert_gps_to_decimal(lat_tag, lat_ref_tag)
                lon_decimal = self._convert_gps_to_decimal(lon_tag, lon_ref_tag)

                if lat_decimal is not None and lon_decimal is not None:
                    if self.validate_coordinates(lat_decimal, lon_decimal):
                        gps_data.update({
                            "GPS Latitude": lat_decimal,  # 数値として返す
                            "GPS Longitude": lon_decimal,  # 数値として返す
                            "GPS Coordinates": self._format_coordinates(
                                lat_decimal, lon_decimal
                            ),
                            "gps_coordinates": (lat_decimal, lon_decimal),
                        })

            # 高度の処理
            if "GPS GPSAltitude" in tags:
                altitude_tag = tags["GPS GPSAltitude"]
                altitude_ref_tag = tags.get("GPS GPSAltitudeRef", "0")

                try:
                    altitude = self._parse_rational(str(altitude_tag))
                    if altitude is not None:
                        # 高度参照（0=海抜、1=海抜以下）
                        if str(altitude_ref_tag) == "1":
                            altitude = -altitude
                        gps_data["GPS Altitude"] = altitude
                except (ValueError, TypeError):
                    pass

            # GPS時刻の処理
            if "GPS GPSTimeStamp" in tags:
                gps_time_tag = tags["GPS GPSTimeStamp"]
                try:
                    # GPSTimeStampは通常 [時, 分, 秒] の形式
                    if hasattr(gps_time_tag, '__iter__'):
                        time_parts = []
                        for part in gps_time_tag:
                            time_parts.append(str(self._parse_rational(str(part))))
                        if len(time_parts) >= 3:
                            gps_data["GPS Timestamp"] = f"{time_parts[0]}:{time_parts[1]}:{time_parts[2]}"
                except (ValueError, TypeError):
                    pass

            # GPS日付の処理
            if "GPS GPSDateStamp" in tags:
                gps_date = str(tags["GPS GPSDateStamp"])
                if gps_date and gps_date != "None":
                    gps_data["GPS Date"] = gps_date

            return gps_data if gps_data else None

        except Exception as e:
            self.logger_system.log_error(AIComponent.COPILOT, e, "gps_extraction", {})

        return None

    def _convert_gps_to_decimal(self, gps_coord: Any, gps_ref: Any) -> Optional[float]:
        """Convert GPS coordinates from DMS to decimal (CS4Coding implementation)"""

        try:
            if not gps_coord or not gps_ref:
                return None

            coord_str = str(gps_coord)

            # Parse coordinate parts
            if "[" in coord_str and "]" in coord_str:
                coord_parts = coord_str.strip("[]").split(", ")
                if len(coord_parts) >= 3:
                    degrees = self._parse_rational(coord_parts[0])
                    minutes = self._parse_rational(coord_parts[1])
                    seconds = self._parse_rational(coord_parts[2])

                    if (
                        degrees is not None
                        and minutes is not None
                        and seconds is not None
                    ):
                        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

                        ref_str = str(gps_ref).upper().strip()
                        if ref_str in ["S", "W"]:
                            decimal = -decimal

                        return decimal

            # Try direct float conversion
            try:
                decimal = float(coord_str)
                ref_str = str(gps_ref).upper().strip()
                if ref_str in ["S", "W"]:
                    decimal = -decimal
                return decimal
            except ValueError:
                pass

            return None

        except Exception:
            return None

    def _parse_rational(self, rational_str: str) -> Optional[float]:
        """Parse a rational number string (CS4Coding implementation)"""

        try:
            rational_str = rational_str.strip()

            if "/" in rational_str:
                numerator, denominator = rational_str.split("/")
                if float(denominator) != 0:
                    return float(numerator) / float(denominator)
            else:
                return float(rational_str)

        except (ValueError, ZeroDivisionError):
            pass

        return None

    def _extract_with_pil(self, path: Path) -> Dict[str, Any]:
        """Extract EXIF using PIL library"""

        exif_data = {}

        try:
            with Image.open(path) as img:
                if hasattr(img, "_getexif"):
                    exif_dict = img._getexif()
                    if exif_dict:
                        exif_data.update(self._parse_pil_exif(exif_dict))

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.COPILOT, e, "pil_exif_extraction", {"file_path": str(path)}
            )

        return exif_data

    def _parse_pil_exif(self, exif_dict: Dict[int, Any]) -> Dict[str, str]:
        """Parse PIL EXIF dictionary"""

        from PIL.ExifTags import TAGS

        parsed = {}

        try:
            for tag_id, value in exif_dict.items():
                tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                parsed[tag_name] = str(value)

        except Exception as e:
            self.logger_system.log_error(AIComponent.COPILOT, e, "pil_exif_parsing", {})

        return parsed

    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats"""
        return self.supported_formats.copy()

    def validate_image(self, path: Path) -> bool:
        """
        Validate if the file is a supported image

        Args:
            path: Path to validate

        Returns:
            True if valid image, False otherwise
        """

        try:
            # Check if file exists
            if not path.exists() or not path.is_file():
                return False

            # Check file extension
            if path.suffix.lower() not in self.supported_formats:
                return False

            # Try to open with PIL for validation
            if PIL_AVAILABLE:
                try:
                    with Image.open(path) as img:
                        img.verify()
                    return True
                except Exception:
                    pass

            # Fallback to basic checks
            return path.stat().st_size > 0

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.COPILOT, e, "image_validation", {"file_path": str(path)}
            )
            return False

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate GPS coordinates"""
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)

    def _format_coordinates(self, lat: float, lon: float, precision: int = 6) -> str:
        """Format coordinates for display"""
        lat_dir = "N" if lat >= 0 else "S"
        lon_dir = "E" if lon >= 0 else "W"
        return f"{abs(lat):.{precision}f}°{lat_dir}, {abs(lon):.{precision}f}°{lon_dir}"

    def _get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get basic file information"""

        try:
            stat_info = path.stat()

            return {
                "File Name": path.name,
                "File Size": self._format_file_size(stat_info.st_size),
                "Modified": datetime.fromtimestamp(stat_info.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Full Path": str(path.absolute()),
                "Extension": path.suffix.lower(),
                "Size Bytes": stat_info.st_size,
            }

        except Exception:
            return {}

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""

        try:
            if size_bytes == 0:
                return "0 B"

            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            size = float(size_bytes)

            while size >= 1024.0 and i < len(size_names) - 1:
                size /= 1024.0
                i += 1

            return f"{size:.1f} {size_names[i]}"

        except Exception:
            return f"{size_bytes} B"

    def _create_image_metadata(
        self, path: Path, exif_data: Dict[str, Any]
    ) -> ImageMetadata:
        """Create ImageMetadata object from EXIF data"""

        try:
            stat_info = path.stat()

            metadata = ImageMetadata(
                file_path=path,
                file_size=stat_info.st_size,
                created_date=datetime.fromtimestamp(stat_info.st_ctime),
                modified_date=datetime.fromtimestamp(stat_info.st_mtime),
                file_format=path.suffix.lower(),
                processing_status=ProcessingStatus.COMPLETED,
                ai_processor=AIComponent.COPILOT,
            )

            # Populate from EXIF data
            metadata.camera_make = exif_data.get("Camera Make")
            metadata.camera_model = exif_data.get("Camera Model")
            metadata.lens_model = exif_data.get("Lens Model")

            # Technical settings
            if "F-Number" in exif_data:
                try:
                    metadata.aperture = float(exif_data["F-Number"].replace("f/", ""))
                except (ValueError, AttributeError):
                    pass

            metadata.shutter_speed = exif_data.get("Exposure Time")

            if "ISO Speed" in exif_data:
                try:
                    metadata.iso = int(exif_data["ISO Speed"])
                except (ValueError, TypeError):
                    pass

            if "Focal Length" in exif_data:
                try:
                    focal_str = exif_data["Focal Length"]
                    if "mm" in focal_str:
                        metadata.focal_length = float(
                            focal_str.replace("mm", "").strip()
                        )
                except (ValueError, AttributeError):
                    pass

            # Image dimensions
            if "Image Width" in exif_data:
                try:
                    metadata.width = int(exif_data["Image Width"])
                except (ValueError, TypeError):
                    pass

            if "Image Height" in exif_data:
                try:
                    metadata.height = int(exif_data["Image Height"])
                except (ValueError, TypeError):
                    pass

            # GPS information
            if "gps_coordinates" in exif_data:
                coords = exif_data["gps_coordinates"]
                metadata.latitude = coords[0]
                metadata.longitude = coords[1]

            return metadata

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO, e, "metadata_creation", {"file_path": str(path)}
            )

            # Return basic metadata on error
            return ImageMetadata(
                file_path=path,
                file_size=0,
                created_date=datetime.now(),
                modified_date=datetime.now(),
                processing_status=ProcessingStatus.FAILED,
                ai_processor=AIComponent.COPILOT,
            )

    def _metadata_to_dict(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Convert ImageMetadata to dictionary"""

        result = {
            "File Name": metadata.file_path.name,
            "File Size": self._format_file_size(metadata.file_size),
            "Modified": metadata.modified_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Full Path": str(metadata.file_path.absolute()),
            "Extension": metadata.file_format,
        }

        if metadata.camera_make:
            result["Camera Make"] = metadata.camera_make
        if metadata.camera_model:
            result["Camera Model"] = metadata.camera_model
        if metadata.lens_model:
            result["Lens Model"] = metadata.lens_model
        if metadata.aperture:
            result["F-Number"] = f"f/{metadata.aperture}"
        if metadata.shutter_speed:
            result["Exposure Time"] = metadata.shutter_speed
        if metadata.iso:
            result["ISO Speed"] = str(metadata.iso)
        if metadata.focal_length:
            result["Focal Length"] = f"{metadata.focal_length}mm"
        if metadata.width:
            result["Image Width"] = str(metadata.width)
        if metadata.height:
            result["Image Height"] = str(metadata.height)

        if metadata.has_gps:
            result["GPS Latitude"] = f"{metadata.latitude:.6f}°"
            result["GPS Longitude"] = f"{metadata.longitude:.6f}°"
            result["GPS Coordinates"] = self._format_coordinates(
                metadata.latitude, metadata.longitude
            )
            result["gps_coordinates"] = (metadata.latitude, metadata.longitude)

        return result

    # Performance monitoring methods (Kiro enhancement)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""

        with self.cache_lock:
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0

            avg_processing_time = (
                sum(self.processing_times) / len(self.processing_times)
                if self.processing_times
                else 0
            )

            return {
                "image_cache_size": len(self.image_cache),
                "metadata_cache_size": len(self.metadata_cache),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": hit_rate,
                "average_processing_time": avg_processing_time,
                "recent_processing_times": self.processing_times[-10:],
                "supported_formats_count": len(self.supported_formats),
                "libraries_available": {
                    "exifread": EXIFREAD_AVAILABLE,
                    "pil": PIL_AVAILABLE,
                    "cv2": CV2_AVAILABLE,
                },
            }

    def clear_cache(self):
        """Clear all caches"""

        with self.cache_lock:
            self.image_cache.clear()
            self.metadata_cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0

        self.logger_system.log_ai_operation(
            AIComponent.KIRO, "cache_clear", "ImageProcessor caches cleared"
        )

    async def process_image_async(self, path: Path) -> Optional[ImageMetadata]:
        """
        Asynchronously process an image and return metadata

        Args:
            path: Path to the image file

        Returns:
            ImageMetadata object or None if failed
        """

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            # Load image
            image = await loop.run_in_executor(self.executor, self.load_image, path)
            if not image:
                return None

            # Extract EXIF data
            exif_data = await loop.run_in_executor(
                self.executor, self.extract_exif, path
            )

            # Create metadata
            metadata = self._create_image_metadata(path, exif_data)

            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "async_image_processing",
                f"Processed {path.name} asynchronously",
            )

            return metadata

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "async_image_processing", "file_path": str(path)},
                AIComponent.COPILOT,
            )
            return None

    def shutdown(self):
        """Shutdown the image processor"""

        try:
            # Shutdown thread pool
            self.executor.shutdown(wait=True)

            # Clear caches
            self.clear_cache()

            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "image_processor_shutdown",
                "CS4Coding ImageProcessor shutdown complete",
            )

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO, e, "image_processor_shutdown", {}
            )
