#!/usr/bin/env python3
"""
PyStreamPDF OCR Integration Example

Demonstrates how to use OCR to handle scanned PDFs before retrieval.
Shows diagnostic → OCR → retrieval workflow.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pystreampdf
from pystreampdf.ocr import process_scanned_pdf, OCRConfig, OCRBackend
from pystreampdf.config import TokenBudgetConfig


def example_ocr_workflow():
    """
    Complete workflow: Diagnose extraction → OCR if needed → Retrieve
    """

    if len(sys.argv) < 2:
        print("Usage: python3 ocr_integration.py <path_to_pdf> [query]")
        print("\nExample:")
        print("  python3 ocr_integration.py scanned_document.pdf 'machine learning'")
        sys.exit(1)

    pdf_path = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "document content"

    print(f"\n{'='*70}")
    print("PyStreamPDF OCR Integration Example")
    print(f"{'='*70}")

    # Step 1: Diagnostic
    print(f"\nStep 1: Diagnostic extraction...")
    print(f"Opening: {pdf_path}")

    try:
        doc = pystreampdf.open(pdf_path)
        print(f"✓ PDF opened ({doc.page_count} pages)")

        # Quick diagnostic with minimal budget
        index = doc.build_index("/tmp/diagnostic_index.db")
        navigator = doc.navigator_with_index(index)

        context, flow = navigator.retrieve_with_flow(
            query, max_tokens=TokenBudgetConfig.get_preset("minimal")
        )

        # Check extraction quality
        extraction_loss = flow.summary.extraction_loss_pct()
        print(f"✓ Diagnostic complete")
        print(f"  Extraction loss: {extraction_loss:.1f}%")
        print(f"  Sections found: {len(context.sections)}")

        # Print per-section diagnostics
        print(f"\nPer-section analysis:")
        for section in flow.sections:
            if section.extraction_diagnosis:
                diag = section.extraction_diagnosis
                print(f"  {section.title} ({section.pages}):")
                print(f"    Loss: {diag.loss_percentage:.1f}%")
                print(f"    Cause: {diag.primary_cause}")
                print(f"    Confidence: {diag.confidence:.0%}")

    except Exception as e:
        print(f"✗ Diagnostic failed: {e}")
        extraction_loss = 50  # Assume high loss if diagnostic fails
        print("  Proceeding with OCR assumption...")

    # Step 2: Decide if OCR needed
    print(f"\nStep 2: Decide on OCR...")

    if extraction_loss < 5:
        print(f"✓ Extraction loss is minimal ({extraction_loss:.1f}%)")
        print("  No OCR needed, proceeding to retrieval...")
        use_ocr = False

    elif extraction_loss < 15:
        print(f"⚠ Moderate extraction loss ({extraction_loss:.1f}%)")
        print("  Consider OCR for better quality")
        use_ocr = True

    else:
        print(f"✗ High extraction loss ({extraction_loss:.1f}%)")
        print("  OCR recommended for acceptable results")
        use_ocr = True

    # Step 3: Apply OCR if needed
    if use_ocr:
        print(f"\nStep 3: Running OCR...")
        print(f"Note: This may take a few minutes for large PDFs")

        try:
            # Auto-detect best available backend
            backend = OCRConfig.auto_detect_backend()
            print(f"Using OCR backend: {backend.value}")

            result = process_scanned_pdf(
                pdf_path,
                output_text_path="/tmp/ocr_output.txt"  # Optional
            )

            print(result.summary())

            if result.pages_failed > 0:
                print(
                    f"⚠ Warning: {result.pages_failed} pages failed OCR, "
                    f"will use partial results"
                )

        except ImportError as e:
            print(f"✗ OCR not available: {e}")
            print("  Install Tesseract or PaddleOCR to enable OCR")
            print("  For now, proceeding with regular extraction...")

    # Step 4: Final retrieval
    print(f"\nStep 4: Final retrieval...")

    doc = pystreampdf.open(pdf_path)
    index = doc.build_index("/tmp/final_index.db")
    navigator = doc.navigator_with_index(index)

    # Use full budget now
    context, flow = navigator.retrieve_with_flow(
        query, max_tokens=TokenBudgetConfig.get_preset("standard")
    )

    print(f"✓ Retrieval complete")
    print(f"  Query: {query}")
    print(f"  Sections retrieved: {len(context.sections)}")
    print(f"  Total tokens: {context.total_tokens}")
    print(f"  Extraction loss: {flow.summary.extraction_loss_pct():.1f}%")

    # Display pipeline visualization
    print(f"\nPipeline visualization:")
    print(flow.to_cli_table())

    # Display retrieved sections
    if context.sections:
        print(f"\nRetrieved sections:")
        for i, section in enumerate(context.sections, 1):
            print(f"\n{i}. {section.heading_path}")
            print(f"   Pages: {section.page_numbers}")
            print(f"   Tokens: ~{section.relevance_score:.0%}")
            print(f"   Content preview: {section.content[:150]}...")
    else:
        print("\n⚠ No sections matched the query")

    print(f"\n{'='*70}")
    print("Example complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    example_ocr_workflow()
