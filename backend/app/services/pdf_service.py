from pathlib import Path

import fitz
from pypdf import PdfReader


class PDFService:
    def count_pages(self, path: Path) -> int:
        return len(PdfReader(str(path)).pages)

    def extract_pages(self, path: Path) -> list[tuple[int, str]]:
        reader = PdfReader(str(path))
        pages: list[tuple[int, str]] = []

        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            cleaned_text = " ".join(text.split())
            if cleaned_text:
                pages.append((index, cleaned_text))

        return pages

    def render_page_images(self, path: Path, zoom: float = 1.6) -> list[tuple[int, bytes]]:
        document = fitz.open(path)
        rendered_pages: list[tuple[int, bytes]] = []

        try:
            matrix = fitz.Matrix(zoom, zoom)
            for index, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                rendered_pages.append((index, pixmap.tobytes("jpeg")))
        finally:
            document.close()

        return rendered_pages


pdf_service = PDFService()
