
"""
Test script for PDF Processor
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_processor import PDFProcessor
import json


def test_pdf_processor():
    """Test the PDF processor with a sample file"""
    
    print("=" * 60)
    print("PDF Processor Test")
    print("=" * 60)
    
    # Initialize processor
    processor = PDFProcessor()
    print(f"✓ Processor initialized")
    print(f"  Temp dir: {processor.temp_dir}")
    print(f"  Upload dir: {processor.upload_dir}")
    
    # Test with a PDF file
    # You'll need to provide a sample PDF
    test_pdf = input("\nEnter path to a PDF file to test (or press Enter to skip): ").strip()
    
    if not test_pdf or not os.path.exists(test_pdf):
        print("\n⚠ No valid PDF provided. Creating sample test...")
        test_file_upload()
        return
    
    print(f"\n📄 Processing: {test_pdf}")
    print("-" * 60)
    
    # Get file info
    print("\n1. Getting file info...")
    file_info = processor.get_file_info(test_pdf)
    print(json.dumps(file_info, indent=2))
    
    # Process the PDF
    print("\n2. Extracting data...")
    result = processor.process_health_report(test_pdf)
    
    # Display results
    print("\n3. Results:")
    print("-" * 60)
    print(f"✓ Pages: {result['num_pages']}")
    print(f"✓ Tables found: {result['num_tables']}")
    print(f"✓ Medical values extracted: {result['num_medical_values']}")
    print(f"✓ Extraction method: {result['extraction_method']}")
    
    # Show sample text
    print("\n4. Sample text (first 500 chars):")
    print("-" * 60)
    print(result['raw_text'][:500])
    print("...")
    
    # Show tables
    if result['tables']:
        print(f"\n5. Tables found: {len(result['tables'])}")
        print("-" * 60)
        for i, table in enumerate(result['tables'][:2], 1):  # Show first 2 tables
            print(f"\nTable {i}:")
            if 'data' in table:
                data = table['data']
                print(f"  Rows: {len(data)}, Cols: {len(data[0]) if data else 0}")
                # Print first few rows
                for row in data[:3]:
                    print(f"  {row}")
            else:
                print(f"  {table}")
    
    # Show medical values
    if result['medical_values']:
        print(f"\n6. Medical values extracted: {len(result['medical_values'])}")
        print("-" * 60)
        for i, value in enumerate(result['medical_values'][:5], 1):  # Show first 5
            print(f"\n  Value {i}:")
            for key, val in value.items():
                print(f"    {key}: {val}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)


def test_file_upload():
    """Test file upload functionality"""
    print("\n" + "=" * 60)
    print("Testing File Upload")
    print("=" * 60)
    
    processor = PDFProcessor()
    
    # Simulate file upload
    sample_content = b"PDF content here"  # This would be actual PDF bytes
    filename = "test_report.pdf"
    
    file_id, temp_path = processor.save_upload(sample_content, filename)
    
    print(f"✓ File saved")
    print(f"  File ID: {file_id}")
    print(f"  Temp path: {temp_path}")
    print(f"  File exists: {os.path.exists(temp_path)}")
    
    # Cleanup
    processor.cleanup(temp_path)
    print(f"✓ Cleanup done")
    print(f"  File still exists: {os.path.exists(temp_path)}")


def test_extraction_methods():
    """Test different extraction methods"""
    print("\n" + "=" * 60)
    print("Available Extraction Methods")
    print("=" * 60)
    
    print("\n1. PDFPlumber:")
    print("   - Fast extraction")
    print("   - Good for structured documents")
    print("   - Excellent table detection")
    
    print("\n2. Unstructured.io:")
    print("   - Slower but more accurate")
    print("   - Better for complex layouts")
    print("   - Handles scanned documents")
    
    print("\n3. Hybrid (Default):")
    print("   - Tries PDFPlumber first")
    print("   - Falls back to Unstructured if needed")
    print("   - Best of both worlds")


if __name__ == "__main__":
    print("\n🏥 Health Navigator - PDF Processor Test\n")
    
    try:
        # Show info about extraction methods
        test_extraction_methods()
        
        # Run main test
        test_pdf_processor()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
