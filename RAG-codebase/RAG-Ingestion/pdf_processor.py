from io import BytesIO
from pypdf import PdfReader


class PDFProcessor:
    def extract_pages(self, pdf_bytes):
        reader = PdfReader(BytesIO(pdf_bytes))
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "page_number": page_number,
                    "text": text
                })
        return pages

"""
Example output for a PDF with 15 pages:
[
    {
        "page_number": 1,
        "text": "..."
    },
    {
        "page_number": 2,
        "text": "..."
    },
    ...
]
"""