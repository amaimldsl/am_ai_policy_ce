#!/usr/bin/env python3
"""
Helper script to extract policy conditions from preprocessed PDF chunks.
This script automates the process of searching for and extracting policy conditions
from all available chunks.
"""

import os
import re
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def find_preprocessed_directory():
    """Find the preprocessed directory from various possible locations"""
    preprocessed_dir_candidates = [
        Path(__file__).resolve().parent / "preprocessed",
        Path(__file__).resolve().parent.parent / "preprocessed",
        Path.cwd() / "preprocessed",
        Path.cwd() / "src" / "pcec" / "preprocessed"
    ]
    
    for candidate in preprocessed_dir_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    # If not found, use the script directory
    return Path(__file__).resolve().parent / "preprocessed"

def find_output_directory():
    """Find or create the output directory"""
    output_dir_candidates = [
        Path(__file__).resolve().parent / "output",
        Path(__file__).resolve().parent.parent / "output",
        Path.cwd() / "output",
        Path.cwd() / "src" / "pcec" / "output"
    ]
    
    for candidate in output_dir_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    # If not found, create in the script directory
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def extract_requirements(text):
    """Extract policy requirements from text"""
    requirements = []
    requirement_keywords = ['shall', 'must', 'should', 'required', 'obligated', 
                           'necessary', 'mandatory', 'comply', 'compliance', 'adhere']
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in requirement_keywords):
            # Extract document reference from nearby lines (usually at the beginning of the chunk)
            doc_ref = "Unknown"
            for j in range(max(0, i-10), i+1):
                if j < len(lines) and "[Document:" in lines[j]:
                    doc_ref = lines[j].strip()
                    break
            
            requirements.append({
                "text": line.strip(),
                "reference": doc_ref
            })
    
    return requirements

def main():
    """Main function to extract conditions from all chunks"""
    preprocessed_dir = find_preprocessed_directory()
    output_dir = find_output_directory()
    
    # Check if preprocessed directory exists and has chunks
    chunks = list(preprocessed_dir.glob("*.txt"))
    if not chunks:
        logger.error("No preprocessed chunks found. Please run document_processor.py first.")
        return 1
    
    logger.info(f"Found {len(chunks)} chunks to process")
    
    # Process all chunks
    all_requirements = []
    condition_id = 1
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)}: {chunk.name}")
        try:
            with open(chunk, "r", encoding="utf-8") as f:
                text = f.read()
            
            chunk_requirements = extract_requirements(text)
            logger.info(f"  Found {len(chunk_requirements)} requirements in chunk")
            
            for req in chunk_requirements:
                all_requirements.append({
                    "id": f"C-{condition_id}",
                    "description": req["text"],
                    "reference": req["reference"]
                })
                condition_id += 1
                
        except Exception as e:
            logger.error(f"  Error processing chunk {chunk.name}: {str(e)}")
    
    # Write the output
    output_file = output_dir / "extracted_conditions.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Extracted Policy Conditions\n\n")
        for req in all_requirements:
            f.write(f"### {req['id']}\n")
            f.write(f"**Description**: {req['description']}\n")
            f.write(f"**Reference**: {req['reference']}\n\n")
    
    logger.info(f"Extracted {len(all_requirements)} policy conditions")
    logger.info(f"Results written to {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
