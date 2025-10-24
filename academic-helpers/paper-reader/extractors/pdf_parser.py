import fitz  # PyMuPDF
from typing import Dict, List, Any


class PDFParser:
    """Parse PDF files using PyMuPDF."""

    def __init__(self):
        """Initialize PDF parser."""
        pass

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse PDF file and extract structured content.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Document dictionary with text, pages, metadata
        """
        doc_obj = fitz.open(pdf_path)

        document = self._create_empty_document()
        document['page_count'] = len(doc_obj)

        # Extract text from all pages
        full_text = []
        pages = []

        for page_num in range(len(doc_obj)):
            page = doc_obj[page_num]
            text = page.get_text()

            pages.append({
                'page_num': page_num + 1,
                'text': text,
                'blocks': self._extract_blocks(page)
            })

            full_text.append(text)

        document['text'] = '\n\n'.join(full_text)
        document['pages'] = pages

        doc_obj.close()
        return document

    def _extract_blocks(self, page) -> List[Dict[str, Any]]:
        """Extract text blocks with font information."""
        blocks = []

        # Get text blocks with font info
        text_dict = page.get_text('dict')

        for block in text_dict.get('blocks', []):
            if 'lines' in block:  # Text block
                for line in block['lines']:
                    for span in line['spans']:
                        blocks.append({
                            'text': span['text'],
                            'font_size': span['size'],
                            'font_name': span['font'],
                            'bbox': span['bbox']
                        })

        return blocks

    def _create_empty_document(self) -> Dict[str, Any]:
        """Create empty document structure."""
        return {
            'text': '',
            'pages': [],
            'page_count': 0
        }
