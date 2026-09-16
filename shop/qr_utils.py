# shop/qr_utils.py
"""
QR code helper for the cashier flow.

Generates the QR as an in-memory PNG and returns it as a base64 data URI,
so it can go straight into <img src="..."> with no MEDIA_ROOT write and no
extra request — important since this app runs on Vercel/Render where the
filesystem is ephemeral (see storage_backends.py / DEPLOYMENT.md).
"""
import base64
from io import BytesIO

import qrcode


def generate_qr_code_data_uri(data: str, box_size: int = 8, border: int = 2) -> str:
    """Return `data` encoded as a QR code, ready to drop into an <img src>."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#151513", back_color="#FFFFFF")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
