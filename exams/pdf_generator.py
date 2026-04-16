import qrcode
import reportlab.lib.pagesizes as pagesizes
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from io import BytesIO
from pathlib import Path
import uuid


# ── Page setup ────────────────────────────────────────
PAGE_W, PAGE_H = pagesizes.A4
MARGIN         = 20 * mm

# ── Bubble settings ───────────────────────────────────
BUBBLE_RADIUS  = 4 * mm
BUBBLE_SPACING = 12 * mm
OPTIONS        = ['A', 'B', 'C', 'D', 'E']
Q_ROW_HEIGHT   = 10 * mm

# ── Anchor settings ───────────────────────────────────
ANCHOR_SIZE    = 10 * mm


def generate_exam_pdf(exam, output_path: str) -> str:
    """
    Generate a printable exam PDF with:
    - Anchor markers at 4 corners
    - Exam info header
    - QR code
    - Bubble grid for all questions

    Returns the path to the generated PDF.
    """
    c = canvas.Canvas(output_path, pagesize=pagesizes.A4)

    # Step 1 — draw anchor markers
    draw_anchors(c)

    # Step 2 — draw header
    draw_header(c, exam)

    # Step 3 — draw QR code
    draw_qr(c, exam)

    # Step 4 — draw bubble grid
    draw_bubbles(c, exam)

    # Step 5 — draw student info box
    draw_student_box(c)

    c.save()
    return output_path


def draw_anchors(c):
    """
    Draw 4 solid black squares at page corners.
    OpenCV detects these to deskew the scanned image.
    """
    c.setFillColor(colors.black)
    positions = [
        (MARGIN, PAGE_H - MARGIN - ANCHOR_SIZE),           # top-left
        (PAGE_W - MARGIN - ANCHOR_SIZE, PAGE_H - MARGIN - ANCHOR_SIZE),  # top-right
        (MARGIN, MARGIN),                                   # bottom-left
        (PAGE_W - MARGIN - ANCHOR_SIZE, MARGIN),           # bottom-right
    ]
    for x, y in positions:
        c.rect(x, y, ANCHOR_SIZE, ANCHOR_SIZE, fill=1, stroke=0)


def draw_header(c, exam):
    """Draw exam title and module info at top."""
    c.setFillColor(colors.black)

    # title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(
        PAGE_W / 2,
        PAGE_H - MARGIN - ANCHOR_SIZE - 15 * mm,
        exam.title
    )

    # module
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        PAGE_W / 2,
        PAGE_H - MARGIN - ANCHOR_SIZE - 22 * mm,
        f"Module: {exam.module.code} — {exam.module.name}"
    )

    # divider line
    y = PAGE_H - MARGIN - ANCHOR_SIZE - 27 * mm
    c.setStrokeColor(colors.black)
    c.line(MARGIN + ANCHOR_SIZE + 5*mm, y, PAGE_W - MARGIN - ANCHOR_SIZE - 5*mm, y)


def draw_qr(c, exam):
    """
    Generate and draw QR code containing:
    EXAM:{exam_id}|STU:{student_placeholder}
    Student ID is written by hand or filled from student list.
    """
    qr_data = f"EXAM:{exam.id}|MOD:{exam.module.code}"

    qr       = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # save QR to buffer
    buffer = BytesIO()
    qr_image.save(buffer, format='PNG')
    buffer.seek(0)

    # draw on PDF
    qr_size = 30 * mm
    qr_x    = PAGE_W - MARGIN - ANCHOR_SIZE - qr_size - 5*mm
    qr_y    = PAGE_H - MARGIN - ANCHOR_SIZE - 60 * mm

    c.drawImage(
        buffer, qr_x, qr_y,
        width=qr_size, height=qr_size,
        preserveAspectRatio=True
    )

    c.setFont("Helvetica", 7)
    c.drawCentredString(qr_x + qr_size/2, qr_y - 4*mm, "Scan code")


def draw_student_box(c):
    """Draw a box for student to write their ID."""
    x = MARGIN + ANCHOR_SIZE + 5*mm
    y = PAGE_H - MARGIN - ANCHOR_SIZE - 62 * mm
    w = 70 * mm
    h = 18 * mm

    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.rect(x, y, w, h, fill=1, stroke=1)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 2*mm, y + h - 6*mm, "Student ID:")
    c.setFont("Helvetica", 9)
    c.drawString(x + 2*mm, y + 4*mm, "Name: ________________________________")


def draw_bubbles(c, exam):
    """
    Draw the bubble grid — one row per question.
    Each row has: question number + 5 bubbles (A B C D E)
    """
    questions = list(exam.questions.all())

    # column header
    start_y  = PAGE_H - MARGIN - ANCHOR_SIZE - 80 * mm
    start_x  = MARGIN + ANCHOR_SIZE + 5 * mm

    # header labels
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawString(start_x, start_y, "Q")
    for i, opt in enumerate(OPTIONS):
        c.drawCentredString(
            start_x + 15*mm + i * BUBBLE_SPACING,
            start_y, opt
        )

    # draw one row per question
    for idx, q in enumerate(questions):
        y = start_y - (idx + 1) * Q_ROW_HEIGHT

        # question number
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(start_x, y, str(q.order))

        # bubbles
        for i, opt in enumerate(OPTIONS):
            bx = start_x + 15*mm + i * BUBBLE_SPACING
            by = y + 1 * mm

            c.setStrokeColor(colors.black)
            c.setFillColor(colors.white)
            c.circle(bx, by, BUBBLE_RADIUS, fill=1, stroke=1)

        # separator line every 5 questions
        if (idx + 1) % 5 == 0:
            c.setStrokeColor(colors.lightgrey)
            c.line(
                start_x, y - 3*mm,
                start_x + 15*mm + 5 * BUBBLE_SPACING, y - 3*mm
            )