from django.core.exceptions import ValidationError
from PIL import Image

LIMIT_MB = 2
VALID_FORMATS = {"JPEG", "PNG", "WEBP"}


def _is_new_upload(image):
    # Las fotos ya guardadas (en el bucket) no se vuelven a validar
    return not getattr(image, "_committed", True)


def validate_image_size(image):
    if not _is_new_upload(image):
        return
    if image.file.size > LIMIT_MB * 1024 * 1024:
        raise ValidationError(f"El archivo no puede exceder {LIMIT_MB}MB")


def validate_image_format(image):
    if not _is_new_upload(image):
        return
    try:
        image.file.seek(0)
        fmt = Image.open(image.file).format
        image.file.seek(0)
    except Exception:
        raise ValidationError("El archivo no es una imagen válida")
    if fmt not in VALID_FORMATS:
        raise ValidationError("Sube una imagen en formato JPEG, PNG o WEBP")


def validate_image_dimensions(image, max_width=1920, max_height=1080):
    if not _is_new_upload(image):
        return
    try:
        image.file.seek(0)
        width, height = Image.open(image.file).size
        image.file.seek(0)
    except Exception:
        raise ValidationError("No se pudo validar las dimensiones de la imagen")
    if width > max_width or height > max_height:
        raise ValidationError(
            f"La imagen no puede ser mayor a {max_width}x{max_height} píxeles"
        )