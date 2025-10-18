
"""
PDF Processor Service
Extracts text, tables, and medical data from health report PDFs
"""

import os
import uuid
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# PDF processing libraries
import pdfplumber

# Try to import unstructured, but make it optional
try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    print("⚠️  Unstructured.io not available - using PDFPlumber only")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Handles PDF upload, extraction, and processing of health reports.
    Uses pdfplumber (fast) and optionally Unstructured.io (accurate).
    """
    
    def __init__(self, temp_dir: str = "temp", upload_dir: str = "uploads"):
        """
        Initialize PDF processor with directories for temporary files.
        
        Args:
            temp_dir: Directory for temporary file processing
            upload_dir: Directory for uploaded files
        """
        self.temp_dir = Path(temp_dir)
        self.upload_dir = Path(upload_dir)
        
        # Create directories if they don't exist
        self.temp_dir.mkdir(exist_ok=True)
        self.upload_dir.mkdir(exist_ok=True)
        
        logger.info(f"PDF Processor initialized. Temp: {temp_dir}, Upload: {upload_dir}")
        if not UNSTRUCTURED_AVAILABLE:
            logger.info("Running in PDFPlumber-only mode")
    
    def save_upload(self, file_content: bytes, filename: str) -> tuple[str, str]:
        """
        Save an uploaded file temporarily.
        
        Args:
            file_content: Binary content of the PDF file
            filename: Original filename
            
        Returns:
            Tuple of (file_id, temp_file_path)
        """
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Get file extension
            file_extension = Path(filename).suffix or ".pdf"
            
            # Create temporary filename
            temp_filename = f"{file_id}{file_extension}"
            temp_path = self.temp_dir / temp_filename
            
            # Save file
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            logger.info(f"Saved upload: {filename} → {temp_path} ({len(file_content)} bytes)")
            
            return file_id, str(temp_path)
            
        except Exception as e:
            logger.error(f"Error saving upload: {e}")
            raise
    
    def extract_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text and tables using pdfplumber (fast, good for structured docs).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text, tables, and metadata
        """
        try:
            logger.info(f"Extracting with pdfplumber: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                # Extract full text
                full_text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"\n--- Page {page_num} ---\n{page_text}"
                
                # Extract tables
                tables = []
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_num, table in enumerate(page_tables, 1):
                            if table:  # Make sure table is not None
                                tables.append({
                                    "page": page_num,
                                    "table_number": table_num,
                                    "data": table,
                                    "rows": len(table),
                                    "cols": len(table[0]) if table else 0
                                })
                
                result = {
                    "text": full_text,
                    "tables": tables,
                    "num_pages": len(pdf.pages),
                    "method": "pdfplumber"
                }
                
                logger.info(f"Extracted {len(tables)} tables from {len(pdf.pages)} pages")
                return result
                
        except Exception as e:
            logger.error(f"Error with pdfplumber: {e}")
            raise
    
    def extract_with_unstructured(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract using Unstructured.io (better for complex layouts).
        Only works if unstructured is properly installed.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted elements organized by type
        """
        if not UNSTRUCTURED_AVAILABLE:
            logger.warning("Unstructured.io not available, skipping")
            return {"text": "", "tables": [], "titles": [], "method": "unavailable"}
        
        try:
            logger.info(f"Extracting with Unstructured: {pdf_path}")
            
            # Partition PDF with hi-res strategy
            elements = partition_pdf(
                filename=pdf_path,
                strategy="fast",  # Changed from "hi_res" to "fast" - faster and fewer dependencies
                infer_table_structure=True,
                extract_images_in_pdf=False,
            )
            
            # Organize elements by type
            text_elements = []
            table_elements = []
            title_elements = []
            
            for element in elements:
                element_dict = element.to_dict()
                element_type = element_dict.get("type")
                
                if element_type == "Table":
                    table_elements.append(element_dict)
                elif element_type == "Title":
                    title_elements.append(element_dict)
                else:
                    text_elements.append(element_dict)
            
            # Combine text
            full_text = "\n".join([e.get("text", "") for e in text_elements if e.get("text")])
            
            result = {
                "text": full_text,
                "tables": table_elements,
                "titles": title_elements,
                "all_elements": len(elements),
                "method": "unstructured"
            }
            
            logger.info(f"Extracted {len(table_elements)} tables, {len(title_elements)} titles")
            return result
            
        except Exception as e:
            logger.error(f"Error with Unstructured: {e}")
            return {"text": "", "tables": [], "titles": [], "method": "error"}
    
    def extract_medical_values(self, tables: List[Dict]) -> List[Dict[str, str]]:
        """
        Extract medical test values from tables.
        Looks for common patterns in lab report tables.
        
        Args:
            tables: List of table dictionaries
            
        Returns:
            List of dictionaries with medical test data
        """
        medical_data = []
        
        try:
            for table_info in tables:
                # Get table data
                if "data" in table_info:
                    rows = table_info["data"]
                elif "text" in table_info:
                    # Unstructured format
                    continue
                else:
                    continue
                
                if not rows or len(rows) < 2:
                    continue
                
                # First row is usually headers
                headers = rows[0]
                
                # Clean headers (remove whitespace, make lowercase)
                headers = [str(h).strip().lower() if h else "" for h in headers]
                
                # Process data rows
                for row in rows[1:]:
                    if len(row) >= len(headers):
                        # Create dictionary from row
                        row_dict = {}
                        for i, header in enumerate(headers):
                            if i < len(row) and row[i]:
                                row_dict[header] = str(row[i]).strip()
                        
                        # Only add if we have some data
                        if row_dict:
                            row_dict["source_page"] = table_info.get("page", "unknown")
                            medical_data.append(row_dict)
            
            logger.info(f"Extracted {len(medical_data)} medical value rows")
            return medical_data
            
        except Exception as e:
            logger.error(f"Error extracting medical values: {e}")
            return []
    
    def process_health_report(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main processing pipeline - tries multiple methods for best results.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with all extracted data
        """
        try:
            logger.info(f"Processing health report: {pdf_path}")
            
            # Step 1: Try pdfplumber first (faster and more reliable)
            result = self.extract_with_pdfplumber(pdf_path)
            
            # Step 2: If no tables found and Unstructured is available, try it
            if not result["tables"] and UNSTRUCTURED_AVAILABLE:
                logger.info("No tables with pdfplumber, trying Unstructured...")
                try:
                    unstructured_result = self.extract_with_unstructured(pdf_path)
                    
                    # Merge results
                    if unstructured_result.get("tables"):
                        result["tables"] = unstructured_result["tables"]
                        result["method"] = "hybrid"
                    
                    # Add titles if found
                    if unstructured_result.get("titles"):
                        result["titles"] = unstructured_result["titles"]
                        
                except Exception as e:
                    logger.warning(f"Unstructured extraction failed: {e}")
            
            # Step 3: Extract medical values from tables
            medical_values = self.extract_medical_values(result["tables"])
            
            # Step 4: Compile final result
            final_result = {
                "raw_text": result["text"],
                "tables": result["tables"],
                "medical_values": medical_values,
                "num_pages": result.get("num_pages", 0),
                "num_tables": len(result["tables"]),
                "num_medical_values": len(medical_values),
                "extraction_method": result["method"],
                "titles": result.get("titles", [])
            }
            
            logger.info(
                f"Processing complete: {final_result['num_pages']} pages, "
                f"{final_result['num_tables']} tables, "
                f"{final_result['num_medical_values']} medical values"
            )
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error processing health report: {e}")
            raise
    
    def cleanup(self, file_path: str) -> bool:
        """
        Remove temporary files after processing.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up: {file_path}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Could not cleanup file {file_path}: {e}")
            return False
    
    def get_file_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get basic information about a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            file_path = Path(pdf_path)
            file_size = file_path.stat().st_size
            
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                
                # Get first page dimensions
                first_page = pdf.pages[0]
                page_width = first_page.width
                page_height = first_page.height
            
            return {
                "filename": file_path.name,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "num_pages": num_pages,
                "page_dimensions": {
                    "width": page_width,
                    "height": page_height
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}


# Convenience function for quick testing
def quick_process(pdf_path: str) -> Dict[str, Any]:
    """
    Quick processing function for testing.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted data
    """
    processor = PDFProcessor()
    return processor.process_health_report(pdf_path)
