"""
Resume parser service to extract text from PDF and DOCX files.
"""
import os
from typing import Dict, Optional
import pdfplumber
import PyPDF2
from docx import Document
import re


class ResumeParser:
    """Parse resume files and extract text content."""

    SUPPORTED_EXTENSIONS = ['.pdf', '.docx']

    def __init__(self):
        """Initialize the resume parser."""
        pass

    def parse_file(self, file_path: str) -> Dict[str, str]:
        """
        Parse a resume file and extract text.

        Args:
            file_path: Path to the resume file

        Returns:
            Dictionary with 'text' and 'filename' keys

        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Extract text based on file type
        if ext == '.pdf':
            text = self._extract_from_pdf(file_path)
        elif ext == '.docx':
            text = self._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        # Clean the extracted text
        text = self._clean_text(text)

        return {
            'text': text,
            'filename': os.path.basename(file_path)
        }

    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file.

        Uses pdfplumber as primary method, falls back to PyPDF2 if needed.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text
        """
        text = ""

        # Try pdfplumber first (better text extraction)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2...")

            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e2:
                raise ValueError(f"Failed to extract text from PDF: {e2}")

        if not text.strip():
            raise ValueError("No text could be extracted from the PDF file")

        return text

    def _extract_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file.

        Args:
            file_path: Path to DOCX file

        Returns:
            Extracted text
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

            if not text.strip():
                raise ValueError("No text could be extracted from the DOCX file")

            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {e}")

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters that might cause issues
        text = text.replace('\x00', '')

        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove multiple consecutive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return text.strip()

    def validate_file(self, file_path: str, max_size_mb: int = 10) -> bool:
        """
        Validate file before parsing.

        Args:
            file_path: Path to file
            max_size_mb: Maximum file size in MB

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValueError(
                f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
            )

        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        return True

    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract basic contact information from resume text.

        This is a simple regex-based extraction. LLM will do more sophisticated extraction.

        Args:
            text: Resume text

        Returns:
            Dictionary with email, phone, linkedin
        """
        contact_info = {
            'email': None,
            'phone': None,
            'linkedin': None
        }

        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info['email'] = email_match.group()

        # Extract phone (US format)
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group()

        # Extract LinkedIn URL
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin'] = linkedin_match.group()

        return contact_info


# Create a singleton instance
resume_parser = ResumeParser()
