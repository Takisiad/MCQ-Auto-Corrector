import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.85
MIN_BUBBLE_FILL      = 0.40


def process_image(image_path: str, bubble_map: dict, questions: list):
    """
    Full OMR pipeline for one scanned exam sheet.
    Returns (answers, confidences, score, is_flagged, flag_reason)
    """
    # Step 1 — load image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")

    # Step 2 — deskew
    aligned = align_to_anchors(image)

    # Step 3 — read QR
    exam_id, student_id = read_qr(aligned)

    # Step 4 — read bubbles
    answers, confidences = read_bubbles(aligned, bubble_map)

    # Step 5 — check confidence
    is_flagged, flag_reason = check_confidence(answers, confidences)

    # Step 6 — calculate score
    score = calculate_score(answers, questions)

    return {
        'exam_id':     exam_id,
        'student_id':  student_id,
        'answers':     answers,
        'confidences': confidences,
        'score':       score,
        'is_flagged':  is_flagged,
        'flag_reason': flag_reason,
    }


def align_to_anchors(image: np.ndarray) -> np.ndarray:
    """
    Detect 4 black anchor squares at paper corners
    and warp image to canonical A4 size.
    """
    gray    = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(
        blurred, 60, 255, cv2.THRESH_BINARY_INV
    )

    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    anchors = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 800 < area < 5000:
            peri   = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(cnt)
                anchors.append((x + w // 2, y + h // 2))

    if len(anchors) < 4:
        logger.warning("Could not detect 4 anchors — skipping deskew")
        return image

    pts    = np.array(anchors[:4], dtype=np.float32)
    src    = sort_corners(pts)
    W, H   = 2100, 2970
    dst    = np.float32([[0,0],[W,0],[W,H],[0,H]])
    M      = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(image, M, (W, H))


def sort_corners(pts: np.ndarray) -> np.ndarray:
    """Sort points: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s    = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def read_qr(image: np.ndarray) -> tuple:
    """
    Read QR code from the exam sheet.
    Returns (exam_id, module_code)
    QR format: EXAM:<id>|MOD:<module_code>
    """
    detector  = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(image)

    if not data:
        raise ValueError("QR code not found")

    parts       = dict(p.split(":", 1) for p in data.split("|") if ":" in p)
    exam_id     = parts.get("EXAM", "")
    module_code = parts.get("MOD", "")

    return exam_id, module_code


def read_bubbles(image: np.ndarray, bubble_map: dict) -> tuple:
    """
    For each question in bubble_map, calculate fill density
    of each bubble and pick the most filled one as the answer.

    bubble_map format:
    {
      "q1": {
        "options": {
          "A": {"x": 120, "y": 340, "w": 20, "h": 20},
          "B": {"x": 155, "y": 340, "w": 20, "h": 20}
        }
      }
    }
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(
        gray, 100, 255, cv2.THRESH_BINARY_INV
    )

    answers     = {}
    confidences = {}

    for q_key, q_data in bubble_map.items():
        densities = {}

        for option, coords in q_data["options"].items():
            x, y, w, h = (
                coords["x"], coords["y"],
                coords["w"], coords["h"]
            )
            roi         = binary[y:y+h, x:x+w]
            density     = float(np.sum(roi > 0)) / (w * h)
            densities[option] = density

        best        = max(densities, key=densities.get)
        best_val    = densities[best]
        sorted_vals = sorted(densities.values(), reverse=True)

        if best_val < MIN_BUBBLE_FILL:
            answers[q_key]     = ""
            confidences[q_key] = 0.0
        else:
            answers[q_key] = best
            if len(sorted_vals) > 1 and sorted_vals[1] > 0:
                conf = sorted_vals[0] / (sorted_vals[0] + sorted_vals[1])
            else:
                conf = 1.0
            confidences[q_key] = round(min(conf, 1.0), 4)

    return answers, confidences


def check_confidence(answers: dict, confidences: dict) -> tuple:
    """
    Flag submission if any question has low confidence
    or too many unanswered questions.
    """
    if not answers:
        return True, "No answers detected"

    low  = [q for q, c in confidences.items() if c < CONFIDENCE_THRESHOLD]
    blank = [q for q, a in answers.items() if not a]

    if low:
        return True, f"Low confidence on: {', '.join(low)}"

    if len(blank) / len(answers) > 0.20:
        return True, f"{len(blank)} questions unanswered"

    return False, ""


def calculate_score(answers: dict, questions: list) -> float:
    """Compare answers to key and sum weights."""
    total = 0.0
    for q in questions:
        key = f"q{q.order}"
        if answers.get(key, "").upper() == q.correct_answer.upper():
            total += q.weight
    return round(total, 2)