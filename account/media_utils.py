from pathlib import Path

from django.conf import settings


def resolve_local_media_path(stored_name, upload_dir=None):
    media_root = Path(settings.MEDIA_ROOT)
    exact_path = media_root / stored_name
    if exact_path.exists():
        return exact_path

    normalized_name = (stored_name or "").replace("\\", "/").strip("/")
    upload_dirs = [upload_dir] if upload_dir else ["profile", "product_image"]

    for current_upload_dir in upload_dirs:
        resolved = _resolve_from_upload_dir(media_root, normalized_name, current_upload_dir)
        if resolved:
            return resolved

    return None


def _resolve_from_upload_dir(media_root, normalized_name, upload_dir):
    upload_marker = f"{upload_dir}/"
    upload_index = normalized_name.find(upload_marker)
    relative_name = normalized_name[upload_index:] if upload_index >= 0 else normalized_name

    direct_relative = media_root / relative_name
    if direct_relative.exists():
        return direct_relative

    search_dir = media_root / upload_dir
    if not search_dir.exists():
        return None

    stem = Path(relative_name).name
    seen_stems = set()

    while stem and stem not in seen_stems:
        seen_stems.add(stem)
        matches = sorted(path for path in search_dir.glob(f"{stem}.*") if path.is_file())
        if matches:
            return matches[0]

        if "_" not in stem:
            break

        stem = stem.rsplit("_", 1)[0]

    return None
