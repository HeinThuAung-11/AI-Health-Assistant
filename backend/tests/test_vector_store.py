
"""
Test Vector Store Manager
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStoreManager
from config import get_ai_config


def test_vector_store():
    print("=" * 70)
    print("Vector Store Test")
    print("=" * 70)
    
    # Get config
    ai_config = get_ai_config()
    
    # Extract report
    print("\n1. Extracting sample report...")
    processor = PDFProcessor()
    extracted = processor.process_health_report("tests/sample_health_report.pdf")
    print(f"✅ Extracted {len(extracted['raw_text'])} characters")
    
    # Create vector store
    print("\n2. Creating vector store...")
    manager = VectorStoreManager(
        api_key=ai_config['api_key'],
        use_groq=(ai_config['provider'] == 'groq')
    )
    
    success = manager.create_report_vectorstore(
        report_id="test-report-123",
        report_text=extracted['raw_text'],
        metadata={"filename": "sample_health_report.pdf"}
    )
    
    if success:
        print("✅ Vector store created!")
    else:
        print("❌ Failed to create vector store")
        return False
    
    # Test search
    print("\n3. Testing search...")
    test_queries = [
        "What is the hemoglobin level?",
        "Tell me about white blood cells",
        "What are the platelets?"
    ]
    
    for query in test_queries:
        print(f"\n   Query: {query}")
        results = manager.search_similar("test-report-123", query, k=2)
        
        for i, result in enumerate(results, 1):
            print(f"   Result {i}: {result['text'][:100]}...")
            print(f"   Score: {result['score']:.4f}")
    
    print("\n" + "=" * 70)
    print("✅ Vector Store test completed!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        test_vector_store()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
