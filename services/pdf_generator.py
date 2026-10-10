import os
import uuid
import logging
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader

from locales import t
from astrology_calculator import sign_display, element_display, quality_display, planet_display

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf")
BACKGROUND_PATH = os.path.join(BASE_DIR, "static", "nate-rayfield-_WR6tUIAJe8-unsplash.jpg")

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont("DejaVuSans", FONT_PATH))
    FONT_NAME = "DejaVuSans"
else:
    FONT_NAME = "Helvetica"

if os.path.exists(FONT_BOLD_PATH):
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_BOLD_PATH))
    FONT_BOLD_NAME = "DejaVuSans-Bold"
else:
    FONT_BOLD_NAME = "Helvetica-Bold"

TEXT_GOLD = HexColor("#FFD700")
TEXT_LIGHT = HexColor("#F0F0F0")
TEXT_WHITE = HexColor("#FFFFFF")
BG_DARK = HexColor("#1a2a3a")
ACCENT_PURPLE = HexColor("#8B5CF6")


class ProfessionalPDFGenerator:
    def _draw_background(self, c, width, height):
        if os.path.exists(BACKGROUND_PATH):
            try:
                img = ImageReader(BACKGROUND_PATH)
                c.drawImage(img, 0, 0, width=width, height=height,
                            preserveAspectRatio=True, mask="auto")
                c.setFillColor(white)
                c.setFillAlpha(0.3)
                c.rect(0, 0, width, height, fill=1)
                c.setFillAlpha(1.0)
                return
            except Exception as e:
                logger.warning(f"Фон не загружен: {e}")
        c.setFillColor(BG_DARK)
        c.rect(0, 0, width, height, fill=1)

    def _draw_decorative_frame(self, c, width, height):
        c.setStrokeColor(ACCENT_PURPLE)
        c.setLineWidth(2)
        c.rect(20, 20, width - 40, height - 40)
        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1)
        c.rect(25, 25, width - 50, height - 50)

    def _draw_text_wrapped(self, c, text, x, y, font, size, max_width, line_height=15):
        """Умный перенос текста."""
        c.setFont(font, size)
        words = text.split()
        line = ""
        for word in words:
            if c.stringWidth(line + word, font, size) < max_width:
                line += word + " "
            else:
                c.drawString(x, y, line.strip())
                y -= line_height
                line = word + " "
        if line.strip():
            c.drawString(x, y, line.strip())
            y -= line_height
        return y

    # ============================================================
    # НАТАЛЬНАЯ КАРТА PDF
    # ============================================================
    def create_natal_chart_pdf(self, chart_data: dict, lang: str = "ru") -> str:
        """PDF натальной карты без символов и markdown."""
        filename = f"natal_report_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        self._draw_background(c, width, height)
        self._draw_decorative_frame(c, width, height)

        # Заголовок
        c.setFont(FONT_BOLD_NAME, 24)
        c.setFillColor(TEXT_GOLD)
        c.drawCentredString(width / 2, height - 55, "НАТАЛЬНАЯ КАРТА")

        info = chart_data.get("birth_info", {})
        c.setFont(FONT_BOLD_NAME, 15)
        c.setFillColor(TEXT_WHITE)
        c.drawCentredString(width / 2, height - 85, info.get("name", "Пользователь"))

        c.setFont(FONT_NAME, 11)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(
            width / 2, height - 105,
            f"{info.get('date', '')} в {info.get('time', '')} | {info.get('place', '')}"
        )

        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1.5)
        c.line(width / 4, height - 120, width * 3 / 4, height - 120)

        y = height - 160

        # Основные характеристики
        c.setFont(FONT_BOLD_NAME, 13)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ОСНОВНЫЕ ХАРАКТЕРИСТИКИ")
        y -= 22
        c.setFont(FONT_NAME, 11)
        c.setFillColor(TEXT_WHITE)
        c.drawString(70, y, f"Солнце в знаке: {chart_data.get('sun_sign', 'Неизвестно')}")
        y -= 18
        c.drawString(70, y, f"Стихия: {chart_data.get('element', 'Неизвестно')}")
        y -= 18
        c.drawString(70, y, f"Качество: {chart_data.get('quality', 'Неизвестно')}")
        y -= 18
        c.drawString(70, y, f"Асцендент: {chart_data.get('ascendant', 'Неизвестно')}")
        y -= 35

        # Планеты — две колонки
        c.setFont(FONT_BOLD_NAME, 13)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "ПОЛОЖЕНИЕ ПЛАНЕТ")
        y -= 22
        c.setFont(FONT_NAME, 10)
        c.setFillColor(TEXT_WHITE)
        planets = chart_data.get("planets", [])
        half = (len(planets) + 1) // 2
        y_left = y
        for p in planets[:half]:
            retro = " (R)" if p.get("retrograde") else ""
            text = f"{planet_display(p.get('name', '?'), lang)}: {sign_display(p.get('sign', '?'), lang)} ({p.get('house', '?')} {t('NATAL_LABEL_HOUSE', lang)}){retro}"
            c.drawString(70, y_left, text)
            y_left -= 16
        y_right = y
        for p in planets[half:]:
            retro = " (R)" if p.get("retrograde") else ""
            text = f"{planet_display(p.get('name', '?'), lang)}: {sign_display(p.get('sign', '?'), lang)} ({p.get('house', '?')} {t('NATAL_LABEL_HOUSE', lang)}){retro}"
            c.drawString(350, y_right, text)
            y_right -= 16
        y = min(y_left, y_right) - 30

        # Дома — 4 колонки
        c.setFont(FONT_BOLD_NAME, 13)
        c.setFillColor(TEXT_GOLD)
        c.drawString(50, y, "АСТРОЛОГИЧЕСКИЕ ДОМА")
        y -= 22
        c.setFont(FONT_NAME, 10)
        c.setFillColor(TEXT_WHITE)
        houses = chart_data.get("houses", [])
        col_width = 130
        for i, h in enumerate(houses):
            col = i % 4
            row = i // 4
            x = 50 + col * col_width
            y_pos = y - row * 16
            c.drawString(x, y_pos, f"{h.get('number', '?')} {t('NATAL_LABEL_HOUSE', lang)}: {sign_display(h.get('sign', '?'), lang)}")
        rows = (len(houses) + 3) // 4
        y = y - rows * 16 - 30

        # AI-интерпретация
        interpretation = chart_data.get("ai_interpretation", "")
        if interpretation:
            c.setFont(FONT_BOLD_NAME, 13)
            c.setFillColor(TEXT_GOLD)
            c.drawString(50, y, "ИНТЕРПРЕТАЦИЯ")
            y -= 22
            c.setFillColor(TEXT_WHITE)
            y = self._draw_text_wrapped(
                c, interpretation, 70, y, FONT_NAME, 10, width - 140, line_height=14
            )

        # Нижний колонтитул
        c.setFont(FONT_NAME, 9)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(
            width / 2, 40,
            t("PDF_FOOTER", lang)
        )
        c.drawCentredString(
            width / 2, 25,
            f"{t('PDF_FOOTER_CREATED', lang)} • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        c.save()
        return filename

    # ============================================================
    # ГОРОСКОП PDF
    # ============================================================
    def create_horoscope_pdf(self, data: dict, lang: str = "ru") -> str:
        filename = f"horoscope_{uuid.uuid4().hex}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        self._draw_background(c, width, height)
        self._draw_decorative_frame(c, width, height)

        c.setFont(FONT_BOLD_NAME, 24)
        c.setFillColor(TEXT_GOLD)
        c.drawCentredString(width / 2, height - 55, "ГОРОСКОП")

        c.setFont(FONT_BOLD_NAME, 15)
        c.setFillColor(TEXT_WHITE)
        c.drawCentredString(width / 2, height - 85, data.get("user_name", "Пользователь"))

        c.setFont(FONT_NAME, 11)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(
            width / 2, height - 105,
            f"Дата: {data.get('date', datetime.now().strftime('%d.%m.%Y'))}"
        )

        c.setStrokeColor(TEXT_GOLD)
        c.setLineWidth(1.5)
        c.line(width / 4, height - 120, width * 3 / 4, height - 120)

        y = height - 160
        c.setFillColor(TEXT_WHITE)
        horoscope_text = data.get("horoscope", "Сегодня звёзды благоволят вам.")
        self._draw_text_wrapped(c, horoscope_text, 50, y, FONT_NAME, 11, width - 100, line_height=16)

        c.setFont(FONT_NAME, 9)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(
            width / 2, 40,
            t("PDF_FOOTER", lang)
        )
        c.drawCentredString(
            width / 2, 25,
            f"{t('PDF_FOOTER_CREATED', lang)} • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        c.save()
        return filename


pdf_gen = ProfessionalPDFGenerator()
