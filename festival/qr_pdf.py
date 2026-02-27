from io import BytesIO
from typing import Iterable

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from .models import PizzaItem, Waiter


def _make_qr_image(value: str):
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(value)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def _wrap_text(
    text: str,
    *,
    font_name: str,
    font_size: int,
    max_width: float,
    max_lines: int = 2,
) -> list[str]:
    words = (text or "").split()
    if not words:
        return [text or ""]

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                break

    remaining_words = words[len(" ".join(lines + [current]).split()):]
    if remaining_words:
        current = f"{current} {' '.join(remaining_words)}"

    if pdfmetrics.stringWidth(current, font_name, font_size) > max_width:
        while current and pdfmetrics.stringWidth(f"{current}...", font_name, font_size) > max_width:
            current = current[:-1]
        current = f"{current}..."

    lines.append(current)
    return lines[:max_lines]


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

        text_x = x + 33 * mm
        max_text_width = label_w - 36 * mm
        flavor_text = f"Sabor: {item.flavor or '-'}"
        flavor_lines = _wrap_text(
            flavor_text,
            font_name="Helvetica",
            font_size=10,
            max_width=max_text_width,
            max_lines=2,
        )

        c.setFont("Helvetica-Bold", 12)
        c.drawString(text_x, y + 25 * mm, item.id)
        c.setFont("Helvetica", 10)
        flavor_y = y + 18 * mm
        for line in flavor_lines:
            c.drawString(text_x, flavor_y, line)
            flavor_y -= 5 * mm

        c.drawString(text_x, flavor_y - 1 * mm, f"Precio: ${item.price}")

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


def build_waiters_labels_pdf(waiters: Iterable[Waiter]) -> bytes:
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

    for waiter in waiters:
        qr_img = _make_qr_image(waiter.code)
        qr_io = BytesIO()
        qr_img.save(qr_io, format="PNG")
        qr_io.seek(0)
        img_reader = ImageReader(qr_io)

        c.rect(x + 2 * mm, y + 2 * mm, label_w - 4 * mm, label_h - 4 * mm)
        c.drawImage(img_reader, x + 4 * mm, y + 6 * mm, 26 * mm, 26 * mm, preserveAspectRatio=True)

        text_x = x + 33 * mm
        max_text_width = label_w - 36 * mm
        name_lines = _wrap_text(
            f"Mesero: {waiter.name}",
            font_name="Helvetica",
            font_size=10,
            max_width=max_text_width,
            max_lines=2,
        )

        c.setFont("Helvetica-Bold", 12)
        c.drawString(text_x, y + 25 * mm, waiter.code)
        c.setFont("Helvetica", 10)
        text_y = y + 18 * mm
        for line in name_lines:
            c.drawString(text_x, text_y, line)
            text_y -= 5 * mm

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
