"""
OCR (Optical Character Recognition) support for PyStreamPDF

Converts scanned PDFs (image-based) to text-extractable PDFs.
Automatic backend selection for optimal performance.
"""

import os
from typing import Optional, List, Tuple
from enum import Enum
import tempfile


class OCRBackend(Enum):
    """Available OCR backends"""
    TESSERACT = "tesseract"
    PADDLE = "paddle"
    CLOUD_GOOGLE = "google_cloud"
    CLOUD_AWS = "aws"


class OCRConfig:
    """Configuration for OCR processing"""

    def __init__(
        self,
        backend: OCRBackend = OCRBackend.TESSERACT,
        language: str = "eng",
        confidence_threshold: float = 0.5,
        page_indices: Optional[List[int]] = None,  # None = all pages
    ):
        """
        Initialize OCR configuration

        Args:
            backend: OCR backend to use
            language: Language code (eng, fra, etc.) - ignored for some backends
            confidence_threshold: Min confidence score to include OCR text (0.0-1.0)
            page_indices: Specific pages to OCR. None = all pages.
        """
        self.backend = backend
        self.language = language
        self.confidence_threshold = confidence_threshold
        self.page_indices = page_indices

    @staticmethod
    def auto_detect_backend() -> OCRBackend:
        """Detect available OCR backend on system"""
        # Try Tesseract first (most common, free)
        if OCRConfig._has_tesseract():
            return OCRBackend.TESSERACT

        # Try PaddleOCR (pure Python, no system deps)
        if OCRConfig._has_paddle():
            return OCRBackend.PADDLE

        raise RuntimeError(
            "OCR engine not available. Install with: pip install pystreampdf[ocr]\n"
            "For system-specific setup, see documentation."
        )

    @staticmethod
    def _has_tesseract() -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            pytesseract.pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    @staticmethod
    def _has_paddle() -> bool:
        """Check if PaddleOCR is available"""
        try:
            import paddleocr
            return True
        except ImportError:
            return False


class OCRProcessor:
    """Process PDFs with OCR to extract text from scanned pages"""

    def __init__(self, config: Optional[OCRConfig] = None):
        """
        Initialize OCR processor

        Args:
            config: OCR configuration. If None, auto-detects best backend.
        """
        if config is None:
            config = OCRConfig(backend=OCRConfig.auto_detect_backend())

        self.config = config
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize the selected OCR backend"""
        if self.config.backend == OCRBackend.TESSERACT:
            self._init_tesseract()
        elif self.config.backend == OCRBackend.PADDLE:
            self._init_paddle()
        else:
            raise NotImplementedError(f"Backend {self.config.backend} not yet implemented")

    def _init_tesseract(self) -> None:
        """Initialize system-optimized OCR backend"""
        try:
            import pytesseract
            self.ocr_engine = pytesseract
            self.ocr_type = "tesseract"
        except ImportError:
            raise ImportError(
                "System OCR engine not installed. Install with:\n"
                "  pip install pystreampdf[ocr]\n"
                "See documentation for system-specific setup instructions."
            )

    def _init_paddle(self) -> None:
        """Initialize pure-Python OCR backend"""
        try:
            from paddleocr import PaddleOCR
            self.ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang=self.config.language.lower(),
            )
            self.ocr_type = "paddle"
        except ImportError:
            raise ImportError(
                "OCR engine not installed. Install with:\n"
                "  pip install pystreampdf[ocr]"
            )

    def process_page(self, image_path: str) -> str:
        """
        Process a single image page with OCR

        Args:
            image_path: Path to image file

        Returns:
            Extracted text
        """
        if self.ocr_type == "tesseract":
            return self._process_tesseract(image_path)
        elif self.ocr_type == "paddle":
            return self._process_paddle(image_path)
        else:
            raise ValueError(f"Unknown OCR type: {self.ocr_type}")

    def _process_tesseract(self, image_path: str) -> str:
        """Process image with system-optimized OCR"""
        try:
            import pytesseract
            text = pytesseract.image_to_string(
                image_path,
                lang=self.config.language,
            )
            return text
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}")

    def _process_paddle(self, image_path: str) -> str:
        """Process image with pure-Python OCR"""
        try:
            result = self.ocr_engine.ocr(image_path, cls=True)

            texts = []
            for line in result:
                for word_box in line:
                    text, confidence = word_box[1]
                    if confidence >= self.config.confidence_threshold:
                        texts.append(text)

            return "\n".join(texts)
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}")

    def process_pdf_pages(self, pdf_path: str) -> Tuple[str, dict]:
        """
        Convert PDF pages to images and apply OCR

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (combined_text, page_results)
            page_results: Dict with per-page statistics
        """
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError(
                "pdf2image not installed. Install with:\n"
                "  pip install pdf2image"
            )

        # Convert PDF to images
        print(f"Converting PDF to images: {pdf_path}")
        try:
            images = convert_from_path(pdf_path)
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")

        # Process each page
        all_text = []
        page_results = {}
        pages_to_process = self.config.page_indices or range(len(images))

        for page_num in pages_to_process:
            if page_num >= len(images):
                print(f"Warning: Page {page_num} not found (PDF has {len(images)} pages)")
                continue

            print(f"Processing page {page_num + 1}/{len(images)}...")

            # Save image temporarily
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                images[page_num].save(tmp.name)
                try:
                    text = self.process_page(tmp.name)
                    word_count = len(text.split())
                    all_text.append(text)
                    page_results[page_num] = {
                        "word_count": word_count,
                        "status": "success",
                    }
                    print(f"  ✓ Page {page_num + 1}: {word_count} words extracted")
                except Exception as e:
                    page_results[page_num] = {
                        "word_count": 0,
                        "status": "failed",
                        "error": str(e),
                    }
                    print(f"  ✗ Page {page_num + 1}: OCR failed ({e})")
                finally:
                    os.unlink(tmp.name)

        combined_text = "\n\n--- Page Break ---\n\n".join(all_text)
        return combined_text, page_results


class OCRResult:
    """Result of OCR processing"""

    def __init__(self, pdf_path: str, ocr_text: str, page_results: dict):
        self.pdf_path = pdf_path
        self.ocr_text = ocr_text
        self.page_results = page_results

    @property
    def total_words_extracted(self) -> int:
        """Total words extracted via OCR"""
        return sum(r.get("word_count", 0) for r in self.page_results.values())

    @property
    def pages_processed(self) -> int:
        """Number of pages successfully processed"""
        return sum(1 for r in self.page_results.values() if r.get("status") == "success")

    @property
    def pages_failed(self) -> int:
        """Number of pages that failed OCR"""
        return sum(1 for r in self.page_results.values() if r.get("status") == "failed")

    def save_to_file(self, output_path: str) -> None:
        """Save OCR text to file"""
        with open(output_path, "w") as f:
            f.write(self.ocr_text)
        print(f"OCR text saved to: {output_path}")

    def summary(self) -> str:
        """Return summary of OCR results"""
        return f"""
OCR Processing Summary
======================
PDF: {self.pdf_path}
Pages processed: {self.pages_processed}/{len(self.page_results)}
Pages failed: {self.pages_failed}
Total words extracted: {self.total_words_extracted}

Per-page results:
{self._format_page_results()}
"""

    def _format_page_results(self) -> str:
        """Format per-page results as table"""
        lines = []
        for page_num in sorted(self.page_results.keys()):
            result = self.page_results[page_num]
            status = result.get("status", "unknown")
            words = result.get("word_count", 0)
            status_icon = "✓" if status == "success" else "✗"
            lines.append(f"  {status_icon} Page {page_num + 1}: {words} words")
        return "\n".join(lines)


def process_scanned_pdf(
    pdf_path: str,
    output_text_path: Optional[str] = None,
    backend: str = "auto",
    language: str = "eng",
) -> OCRResult:
    """
    Convenience function to process a scanned PDF with OCR

    Args:
        pdf_path: Path to PDF file
        output_text_path: Path to save extracted text. If None, not saved.
        backend: OCR backend ("auto", "tesseract", "paddle")
        language: Language code ("eng", "fra", etc.)

    Returns:
        OCRResult with extracted text and statistics
    """
    # Determine backend
    if backend == "auto":
        backend_enum = OCRConfig.auto_detect_backend()
    else:
        try:
            backend_enum = OCRBackend[backend.upper()]
        except KeyError:
            raise ValueError(f"Unknown backend: {backend}")

    # Configure and process
    config = OCRConfig(backend=backend_enum, language=language)
    processor = OCRProcessor(config)

    print(f"Using OCR backend: {backend_enum.value}")
    ocr_text, page_results = processor.process_pdf_pages(pdf_path)

    # Create result
    result = OCRResult(pdf_path, ocr_text, page_results)

    # Save if requested
    if output_text_path:
        result.save_to_file(output_text_path)

    # Print summary
    print(result.summary())

    return result
