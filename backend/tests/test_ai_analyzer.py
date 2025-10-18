
"""
Test script for AI Analyzer (supports OpenAI and Groq)
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_processor import PDFProcessor
from services.ai_analyzer import HealthReportAnalyzer
from config import get_settings, get_ai_config
import json


def test_analyzer():
    """Test the AI analyzer with extracted data"""
    
    print("=" * 70)
    print("AI Analyzer Test")
    print("=" * 70)
    
    # Get AI configuration
    try:
        ai_config = get_ai_config()
        provider = ai_config["provider"]
        api_key = ai_config["api_key"]
        model = ai_config["model"]
        
        if not api_key:
            print(f"\n❌ Error: {provider.upper()} API key not set!")
            print(f"Please add your API key to backend/.env file:")
            if provider == "groq":
                print("GROQ_API_KEY=gsk-your-actual-key-here")
                print("\nGet free key from: https://console.groq.com/keys")
            else:
                print("OPENAI_API_KEY=sk-your-actual-key-here")
            return False
        
        print(f"✓ Using {provider.upper()} with model: {model}")
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    # Step 1: Extract data from PDF
    print("\n" + "-" * 70)
    print("Step 1: Extracting data from sample PDF...")
    print("-" * 70)
    
    pdf_path = "tests/sample_health_report.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Sample PDF not found: {pdf_path}")
        print("Run: python tests/create_sample_pdf.py")
        return False
    
    processor = PDFProcessor()
    extracted_data = processor.process_health_report(pdf_path)
    
    print(f"✓ Extracted {extracted_data['num_tables']} tables")
    print(f"✓ Found {extracted_data['num_medical_values']} medical values")
    
    # Step 2: Analyze with AI
    print("\n" + "-" * 70)
    print(f"Step 2: Analyzing with {provider.upper()} (this may take 10-20 seconds)...")
    print("-" * 70)
    
    analyzer = HealthReportAnalyzer(
        api_key=api_key,
        model=model,
        temperature=ai_config["temperature"],
        max_tokens=ai_config["max_tokens"],
        use_groq=(provider == "groq")
    )
    
    analysis_result = analyzer.analyze_report(extracted_data)
    
    # Step 3: Display results
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)
    
    print(f"\n📋 Report Type: {analysis_result.get('report_type', 'Unknown')}")
    print(f"👤 Patient: {analysis_result.get('patient_name', 'N/A')}")
    print(f"📅 Date: {analysis_result.get('date', 'N/A')}")
    print(f"🤖 Provider: {analysis_result.get('provider', 'N/A').upper()}")
    print(f"🔍 Confidence: {analysis_result.get('confidence_score', 0.0):.0%}")
    
    urgency = analysis_result.get('urgency', 'routine')
    urgency_emoji = {"routine": "✅", "moderate": "⚠️", "urgent": "🚨"}.get(urgency, "")
    print(f"{urgency_emoji} Urgency: {urgency.upper()}")
    
    # Summary
    print("\n" + "-" * 70)
    print("📝 SUMMARY (in plain English):")
    print("-" * 70)
    print(analysis_result.get('summary', 'No summary available'))
    
    # Key findings
    key_findings = analysis_result.get('key_findings', [])
    if key_findings:
        print("\n" + "-" * 70)
        print(f"🔬 KEY FINDINGS ({len(key_findings)} tests):")
        print("-" * 70)
        
        for i, finding in enumerate(key_findings, 1):
            status = finding.get('status', 'unknown')
            status_emoji = {
                'normal': '✅',
                'elevated': '⬆️',
                'low': '⬇️',
                'critical': '🚨'
            }.get(status, '❓')
            
            print(f"\n{i}. {status_emoji} {finding.get('metric', 'Unknown')}")
            print(f"   Result: {finding.get('value', 'N/A')} {finding.get('unit', '')}")
            print(f"   Normal: {finding.get('range', 'N/A')}")
            print(f"   Status: {status.upper()}")
    
    # Next steps
    next_steps = analysis_result.get('next_steps', [])
    if next_steps:
        print("\n" + "-" * 70)
        print("📋 RECOMMENDED NEXT STEPS:")
        print("-" * 70)
        for i, step in enumerate(next_steps, 1):
            print(f"{i}. {step}")
    
    print("\n" + "=" * 70)
    print("✅ AI Analyzer test completed successfully!")
    print("=" * 70)
    
    # Save results
    output_file = "tests/analysis_result.json"
    with open(output_file, 'w') as f:
        json.dump(analysis_result, f, indent=2)
    print(f"\n💾 Full results saved to: {output_file}")
    
    return True


if __name__ == "__main__":
    print("\n🤖 Health Navigator - AI Analyzer Test\n")
    
    try:
        success = test_analyzer()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
