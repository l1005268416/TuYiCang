import exifread
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_exif(image_path, use_mtime_fallback=True):
    result = {
        'shoot_time': None,
        'camera_model': None,
        'gps': None,
        'resolution': None,
    }

    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        if 'EXIF DateTimeOriginal' in tags:
            dt_str = str(tags['EXIF DateTimeOriginal'])
            try:
                dt = datetime.strptime(dt_str.strip(), "%Y:%m:%d %H:%M:%S")
                result['shoot_time'] = dt.isoformat(timespec='seconds')
            except ValueError:
                pass

        if 'Make' in tags or 'Model' in tags:
            make = str(tags.get('Make', '')).strip()
            model = str(tags.get('Model', '')).strip()
            result['camera_model'] = f"{make} {model}".strip() or None

        if 'GPS GPSLatitude' in tags and 'GPS GPSLatitudeRef' in tags:
            try:
                lat = _convert_ratio_to_deg(tags['GPS GPSLatitude'])
                lat_ref = str(tags['GPS GPSLatitudeRef']).strip()
                lon = _convert_ratio_to_deg(tags.get('GPS GPSLongitude', 0))
                lon_ref = str(tags.get('GPS GPSLongitudeRef', 'E')).strip()

                if lat_ref not in ('N', 'S'):
                    lat = -lat
                if lon_ref not in ('E', 'W'):
                    lon = -lon

                result['gps'] = f"{lat:.4f},{lon:.4f}"
            except Exception:
                pass

        if 'EXIF PixelXDimension' in tags and 'EXIF PixelYDimension' in tags:
            w = int(tags['EXIF PixelXDimension'])
            h = int(tags['EXIF PixelYDimension'])
            result['resolution'] = f"{w}x{h}"

        if result['shoot_time'] is None and use_mtime_fallback:
            import os
            mtime = os.path.getmtime(image_path)
            result['shoot_time'] = datetime.fromtimestamp(mtime).isoformat(timespec='seconds')

    except Exception as e:
        logger.warning("Failed to parse EXIF for %s: %s", image_path, e)

    return result


def _convert_ratio_to_deg(value):
    if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
        return float(value.numerator) / float(value.denominator)
    return 0.0
