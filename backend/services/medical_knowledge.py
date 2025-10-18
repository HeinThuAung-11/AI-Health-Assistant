# services/medical_knowledge.py
from typing import Dict, List

class MedicalKnowledgeBase:
    """Enhanced medical knowledge for better interpretations"""
    
    # Common test reference ranges (these should ideally come from a medical database)
    REFERENCE_RANGES = {
        "hemoglobin": {
            "male": {"min": 13.5, "max": 17.5, "unit": "g/dL"},
            "female": {"min": 12.0, "max": 15.5, "unit": "g/dL"}
        },
        "white_blood_cells": {"min": 4.5, "max": 11.0, "unit": "x10³/μL"},
        "platelets": {"min": 150, "max": 400, "unit": "x10³/μL"},
        "glucose_fasting": {"min": 70, "max": 100, "unit": "mg/dL"},
        "cholesterol_total": {"min": 125, "max": 200, "unit": "mg/dL"},
        "ldl_cholesterol": {"min": 0, "max": 100, "unit": "mg/dL"},
        "hdl_cholesterol": {"min": 40, "max": 999, "unit": "mg/dL"},
        "triglycerides": {"min": 0, "max": 150, "unit": "mg/dL"},
    }
    
    # Common test name variations (for matching)
    TEST_NAME_MAPPINGS = {
        "hgb": "hemoglobin",
        "hb": "hemoglobin",
        "wbc": "white_blood_cells",
        "plt": "platelets",
        "glucose": "glucose_fasting",
        "chol": "cholesterol_total",
    }
    
    @classmethod
    def normalize_test_name(cls, test_name: str) -> str:
        """Normalize test name for matching"""
        normalized = test_name.lower().strip().replace(" ", "_")
        return cls.TEST_NAME_MAPPINGS.get(normalized, normalized)
    
    @classmethod
    def get_reference_range(cls, test_name: str, gender: str = "male") -> Dict:
        """Get reference range for a test"""
        normalized_name = cls.normalize_test_name(test_name)
        range_data = cls.REFERENCE_RANGES.get(normalized_name)
        
        if isinstance(range_data, dict) and gender in range_data:
            return range_data[gender]
        return range_data
    
    @classmethod
    def assess_value_status(cls, test_name: str, value: float, gender: str = "male") -> str:
        """Determine if a value is normal, elevated, low, or critical"""
        ref_range = cls.get_reference_range(test_name, gender)
        
        if not ref_range:
            return "unknown"
        
        min_val = ref_range.get("min", 0)
        max_val = ref_range.get("max", float('inf'))
        
        if value < min_val * 0.7 or value > max_val * 1.5:
            return "critical"
        elif value < min_val:
            return "low"
        elif value > max_val:
            return "elevated"
        else:
            return "normal"