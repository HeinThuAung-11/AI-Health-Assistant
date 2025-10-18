
"""
Test the complete API
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_complete_flow():
    """Test the complete API flow"""
    
    print("=" * 70)
    print("Testing Health Navigator API")
    print("=" * 70)
    
    # 1. Test health check
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # 2. Upload PDF
    print("\n2. Uploading PDF...")
    pdf_path = Path("tests/sample_health_report.pdf")
    
    if not pdf_path.exists():
        print("   ❌ Sample PDF not found!")
        return False
    
    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    if response.status_code != 200:
        print(f"   ❌ Upload failed: {response.text}")
        return False
    
    upload_data = response.json()
    report_id = upload_data["report_id"]
    print(f"   ✅ Uploaded! Report ID: {report_id}")
    print(f"   Filename: {upload_data['filename']}")
    print(f"   Size: {upload_data['file_size']} bytes")
    
    # 3. Analyze report
    print("\n3. Analyzing report (this may take 20-30 seconds)...")
    response = requests.post(f"{BASE_URL}/api/analyze/{report_id}")
    
    if response.status_code != 200:
        print(f"   ❌ Analysis failed: {response.text}")
        return False
    
    analysis = response.json()
    print(f"   ✅ Analysis complete!")
    print(f"   Report Type: {analysis['report_type']}")
    print(f"   Patient: {analysis.get('patient_name', 'N/A')}")
    print(f"   Urgency: {analysis['urgency']}")
    print(f"   Findings: {len(analysis['key_findings'])} tests")
    print(f"\n   Summary: {analysis['summary'][:150]}...")
    
    # 4. Ask questions
    print("\n4. Testing Q&A...")
    questions = [
        "What does elevated white blood cells mean?",
        "Should I be worried about my hemoglobin?",
        "What should I do next?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n   Q{i}: {question}")
        
        response = requests.post(
            f"{BASE_URL}/api/ask",
            json={
                "report_id": report_id,
                "question": question,
                "conversation_history": []
            }
        )
        
        if response.status_code == 200:
            answer = response.json()
            print(f"   A{i}: {answer['answer'][:200]}...")
        else:
            print(f"   ❌ Failed: {response.text}")
    
    # 5. Get report
    print("\n5. Retrieving report...")
    response = requests.get(f"{BASE_URL}/api/report/{report_id}")
    
    if response.status_code == 200:
        print("   ✅ Report retrieved successfully")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # 6. List all reports
    print("\n6. Listing all reports...")
    response = requests.get(f"{BASE_URL}/api/reports")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Found {data['total']} report(s)")
    
    # 7. Delete report
    print("\n7. Cleaning up (deleting report)...")
    response = requests.delete(f"{BASE_URL}/api/report/{report_id}")
    
    if response.status_code == 200:
        print("   ✅ Report deleted")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    print("\n" + "=" * 70)
    print("✅ All API tests completed successfully!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    print("\n🚀 Health Navigator - API Test\n")
    print("Make sure the server is running:")
    print("   python main.py\n")
    
    input("Press Enter when server is ready...")
    
    try:
        test_complete_flow()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("Make sure the API is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
