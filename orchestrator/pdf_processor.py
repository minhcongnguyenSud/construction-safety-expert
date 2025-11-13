"""PDF processor for adding safety documents to knowledge base."""

import re
from typing import List, Dict, Any
from pathlib import Path


class PDFProcessor:
    """Process PDF files and extract clean safety content."""

    # Common unwanted sections to remove
    UNWANTED_PATTERNS = [
        r"table of contents",
        r"list of figures",
        r"list of tables",
        r"index",
        r"references",
        r"bibliography",
        r"works cited",
        r"appendix [a-z]",
        r"appendices",
        r"acknowledgments?",
        r"about the author",
        r"author bio",
        r"copyright",
        r"all rights reserved",
        r"isbn",
        r"published by",
        r"publisher",
        r"disclaimer",
        r"glossary",
        r"further reading",
        r"resources",
        r"^preface$",
        r"^foreword$",
        r"^introduction$",
        r"endnotes?",
        r"footnotes?",
    ]

    # Page markers and headers/footers
    PAGE_MARKERS = [
        r"page \d+",
        r"^\d+$",  # Standalone page numbers
        r"^\d+\s*\|",  # Page number with separator
        r"\|\s*\d+$",  # Page number at end
        r"^page \d+ of \d+",
        r"^\d+\s*/\s*\d+$",  # Page numbers like "1 / 10"
        r"^chapter \d+$",
        r"^section \d+$",
    ]

    def __init__(self):
        """Initialize the PDF processor."""
        self.min_chunk_size = 200  # Minimum characters per chunk
        self.max_chunk_size = 2000  # Maximum characters per chunk

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content

        Raises:
            ImportError: If PyPDF2 is not installed
            FileNotFoundError: If PDF file doesn't exist
        """
        try:
            import PyPDF2
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF processing. "
                "Install it with: pip install PyPDF2"
            )

        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        text_content = []

        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)
                except Exception as e:
                    print(f"Warning: Could not extract text from page {page_num + 1}: {e}")

        return "\n\n".join(text_content)

    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing unwanted sections.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Convert to lowercase for pattern matching
        text_lower = text.lower()

        # Find and remove unwanted sections
        for pattern in self.UNWANTED_PATTERNS:
            # Find section headers
            matches = list(re.finditer(pattern, text_lower))
            for match in reversed(matches):  # Remove from end to maintain indices
                # Try to find the end of this section (next section header or end)
                start = match.start()

                # Remove section header and some content after it
                # Look for next major section (typically all caps or numbered)
                next_section = re.search(
                    r'\n\n[A-Z][A-Z\s]{10,}|\n\n\d+\.\s+[A-Z]',
                    text[start + 100:start + 1000]
                )

                if next_section:
                    end = start + 100 + next_section.start()
                else:
                    end = min(start + 500, len(text))  # Remove up to 500 chars

                text = text[:start] + text[end:]

        # Remove page markers and headers/footers
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line_lower = line.lower().strip()

            # Skip if matches page marker patterns
            if any(re.match(pattern, line_lower) for pattern in self.PAGE_MARKERS):
                continue

            # Skip very short lines that are likely headers/footers
            if len(line.strip()) < 10 and not line.strip().isdigit():
                continue

            cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # Remove repeated content (common in headers/footers)
        text = self._remove_repeated_content(text)

        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
        text = re.sub(r' {2,}', ' ', text)  # Max 1 space
        text = text.strip()

        return text

    def _remove_repeated_content(self, text: str) -> str:
        """Remove repeated sentences or paragraphs.

        Args:
            text: Input text

        Returns:
            Text with repetitions removed
        """
        paragraphs = text.split('\n\n')
        seen = set()
        unique_paragraphs = []

        for para in paragraphs:
            para_clean = para.strip().lower()

            # Skip if we've seen this paragraph before
            if para_clean in seen:
                continue

            # Skip very short paragraphs (likely headers)
            if len(para_clean) < 30:
                unique_paragraphs.append(para)
                continue

            seen.add(para_clean)
            unique_paragraphs.append(para)

        return '\n\n'.join(unique_paragraphs)

    def chunk_text(self, text: str, category: str = "general") -> List[Dict[str, Any]]:
        """Chunk cleaned text into knowledge base documents.

        Args:
            text: Cleaned text content
            category: Category for the chunks

        Returns:
            List of document dictionaries
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        chunks = []
        current_chunk = ""
        current_title = "Safety Information"

        for para in paragraphs:
            # Check if this looks like a section header
            if self._is_section_header(para):
                # Save current chunk if it's substantial
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        "title": current_title,
                        "content": current_chunk.strip(),
                        "category": category
                    })

                # Start new chunk with new title
                current_title = para[:100]  # Limit title length
                current_chunk = ""
                continue

            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += para

            # If chunk is getting large, save it
            if len(current_chunk) >= self.max_chunk_size:
                chunks.append({
                    "title": current_title,
                    "content": current_chunk.strip(),
                    "category": category
                })
                current_chunk = ""
                current_title = "Safety Information (continued)"

        # Add final chunk
        if len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "title": current_title,
                "content": current_chunk.strip(),
                "category": category
            })

        return chunks

    def _is_section_header(self, text: str) -> bool:
        """Check if text looks like a section header.

        Args:
            text: Text to check

        Returns:
            True if looks like a section header
        """
        # Short and mostly uppercase
        if len(text) < 100 and text.isupper():
            return True

        # Starts with number and colon or period
        if re.match(r'^\d+[\.:]\s+[A-Z]', text):
            return True

        # All caps words
        if len(text) < 100 and len(re.findall(r'\b[A-Z]{2,}\b', text)) >= 2:
            return True

        return False

    def process_pdf(
        self,
        pdf_path: str,
        category: str = "general"
    ) -> List[Dict[str, Any]]:
        """Complete PDF processing pipeline.

        Args:
            pdf_path: Path to PDF file
            category: Category for the documents

        Returns:
            List of processed knowledge base documents
        """
        print(f"📄 Extracting text from: {pdf_path}")
        raw_text = self.extract_text_from_pdf(pdf_path)

        print(f"✨ Cleaning text ({len(raw_text)} characters)")
        cleaned_text = self.clean_text(raw_text)

        print(f"📦 Chunking into documents ({len(cleaned_text)} characters)")
        chunks = self.chunk_text(cleaned_text, category)

        print(f"✅ Created {len(chunks)} knowledge base documents")

        return chunks

    def save_chunks_to_file(self, chunks: List[Dict[str, Any]], output_path: str):
        """Save processed chunks to a Python file.

        Args:
            chunks: List of document dictionaries
            output_path: Path to save the Python file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Auto-generated knowledge base from PDF\n\n")
            f.write("KNOWLEDGE_BASE = [\n")

            for chunk in chunks:
                f.write("    {\n")
                f.write(f'        "title": """{chunk["title"]}""",\n')
                f.write(f'        "content": """{chunk["content"]}""",\n')
                f.write(f'        "category": "{chunk["category"]}"\n')
                f.write("    },\n")

            f.write("]\n")

        print(f"💾 Saved to: {output_path}")
