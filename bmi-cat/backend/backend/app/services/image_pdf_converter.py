import base64
import binascii
import io
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException


class ImagePdfConverter:
    # Decode image bytes, never trust extensions or upload MIME types.
    def convert(self, encoded):
        try:
            raw = base64.b64decode(encoded, validate=True)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('size')
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(raw)) as original:
                    if original.format not in ('JPEG', 'PNG', 'WEBP') or original.width * original.height > 24000000:
                        raise ValueError('format or dimensions')
                    original.load()
                    oriented = ImageOps.exif_transpose(original)
                    image = Image.new('RGB', oriented.size, 'white')
                    if 'A' in oriented.getbands():
                        image.paste(oriented, mask=oriented.getchannel('A'))
                    else:
                        image.paste(oriented.convert('RGB'))
                    image.thumbnail((3000, 3000))
                    pdf = io.BytesIO()
                    image.save(pdf, format='PDF', resolution=150.0, title='BMI Cat - dokument')
                    preview = io.BytesIO()
                    image.save(preview, format='JPEG', quality=92)
                    return preview.getvalue(), pdf.getvalue()
        except (ValueError, binascii.Error, OSError, UnidentifiedImageError,
                Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise HTTPException(422, 'Wybierz zdjęcie JPG, PNG lub WebP do 8 MB i 24 megapikseli.') from None
