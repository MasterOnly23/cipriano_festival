from io import BytesIO
from typing import Iterable

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import PizzaItem


def _make_qr_image(value: str):
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(value)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def build_labels_pdf(items: Iterable[PizzaItem]) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    cols = 3
    rows = 8
    label_w = width / cols
    label_h = height / rows

    x = 0
    y = height - label_h
    count = 0

    for item in items:
        qr_img = _make_qr_image(item.id)
        qr_io = BytesIO()
        qr_img.save(qr_io, format="PNG")
        qr_io.seek(0)
        img_reader = ImageReader(qr_io)

        c.rect(x + 2 * mm, y + 2 * mm, label_w - 4 * mm, label_h - 4 * mm)
        c.drawImage(img_reader, x + 4 * mm, y + 6 * mm, 26 * mm, 26 * mm, preserveAspectRatio=True)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(x + 33 * mm, y + 25 * mm, item.id)
        c.setFont("Helvetica", 10)
        c.drawString(x + 33 * mm, y + 18 * mm, f"Sabor: {item.flavor or '-'}")
        c.drawString(x + 33 * mm, y + 12 * mm, f"Precio: ${item.price}")

        count += 1
        x += label_w
        if count % cols == 0:
            x = 0
            y -= label_h
        if count % (cols * rows) == 0:
            c.showPage()
            x = 0
            y = height - label_h

    c.save()
    return buf.getvalue()
