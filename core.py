import os
import re

from rapidocr_onnxruntime import RapidOCR

PHONE_RE = re.compile(
    r"\(?\d{3}\)?[\s.\-xXext]*\d{3}[\s.\-]*\d{4}"
)
ALL_CAPS_RE = re.compile(r"^[A-Z][A-Z&.\s'\-/]+$")
DIGIT_RE = re.compile(r"\d")


class Lead:
    __slots__ = ("name", "category", "address", "phone")

    def __init__(self, name="", category="", address="", phone=""):
        self.name = name
        self.category = category
        self.address = address
        self.phone = phone

    def as_row(self):
        return [self.name, self.category, self.address, self.phone]

    def dedup_key(self):
        return (
            re.sub(r"\s+", " ", self.name).strip().lower(),
            re.sub(r"\s+", " ", self.address).strip().lower(),
            re.sub(r"\D", "", self.phone),
        )


class Scraper:
    def __init__(self):
        self._ocr = None

    def _get_ocr(self):
        if self._ocr is None:
            self._ocr = RapidOCR()
        return self._ocr

    def extract(self, image_path):
        result, _ = self._get_ocr()(image_path)
        if not result:
            return Lead()
        boxes = []
        for box, text, _score in result:
            ys = [p[1] for p in box]
            xs = [p[0] for p in box]
            boxes.append((min(ys), min(xs), max(ys), max(xs), text))
        boxes.sort(key=lambda b: (round((b[0] + b[2]) / 2 / 6), b[1]))
        return self._parse([b[4] for b in boxes])

    def _parse(self, lines):
        lines = [l.strip() for l in lines if l and l.strip()]
        if not lines:
            return Lead()

        phone_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if PHONE_RE.search(lines[i]) and DIGIT_RE.search(lines[i]):
                phone_idx = i
                break

        limit = phone_idx if phone_idx is not None else len(lines)

        category_idx = None
        for i in range(limit):
            if self._is_category(lines[i]):
                category_idx = i

        if category_idx is not None:
            name = re.sub(r"\s+", " ", " ".join(lines[:category_idx])).strip()
            category = lines[category_idx]
            if phone_idx is not None:
                address = re.sub(r"\s+", " ", " ".join(lines[category_idx + 1:phone_idx])).strip()
            else:
                address = re.sub(r"\s+", " ", " ".join(lines[category_idx + 1:])).strip()
        else:
            name = ""
            category = ""
            if phone_idx is not None and phone_idx > 0:
                name = re.sub(r"\s+", " ", " ".join(lines[:phone_idx - 1])).strip()
                address = lines[phone_idx - 1]
            else:
                address = ""

        phone = lines[phone_idx] if phone_idx is not None else ""
        return Lead(name=name, category=category, address=address, phone=self._clean_phone(phone))

    @staticmethod
    def _is_category(line):
        if len(line) < 2:
            return False
        if DIGIT_RE.search(line):
            return False
        return bool(ALL_CAPS_RE.match(line))

    @staticmethod
    def _looks_like_address(line):
        if not line:
            return False
        return (" " in line or "," in line or len(line) > 12)

    @staticmethod
    def _clean_phone(phone):
        if not phone:
            return ""
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        if len(digits) == 11 and digits.startswith("1"):
            d = digits[1:]
            return f"({d[:3]}) {d[3:6]}-{d[6:]}"
        return phone.strip()


def dedupe(leads):
    seen = set()
    out = []
    for lead in leads:
        key = lead.dedup_key()
        if key in seen:
            continue
        seen.add(key)
        out.append(lead)
    return out


def scrape_folder(folder, progress_cb=None):
    images = [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".gif"))
    ]
    return scrape_images(images, progress_cb)


def scrape_images(images, progress_cb=None):
    scraper = Scraper()
    leads = []
    total = len(images)
    for i, img in enumerate(images, start=1):
        try:
            leads.append(scraper.extract(img))
        except Exception:
            leads.append(Lead())
        if progress_cb:
            progress_cb(i, total, os.path.basename(img))
    return [l.as_row() for l in dedupe(leads)]