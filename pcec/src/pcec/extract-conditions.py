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
    """Extract policy requirements from text - ENHANCED VERSION"""
    requirements = []
    
    # Expanded list of requirement keywords for more comprehensive extraction
    requirement_keywords = [
        'shall', 'must', 'should', 'required', 'obligated', 
        'necessary', 'mandatory', 'comply', 'compliance', 'adhere',
        'ensure', 'maintain', 'establish', 'implement', 'provide',
        'responsible', 'accountable', 'follow', 'conduct', 'perform',
        'review', 'verify', 'document', 'record', 'report',
        'complete', 'submit', 'authorize', 'approve', 'prohibit',
        'restrict', 'limit', 'safeguard', 'protect', 'prevent'
    ]
    
    # Add negation patterns to catch requirements phrased as prohibitions
    prohibition_patterns = [
        'not allowed', 'not permitted', 'prohibited', 'shall not',
        'must not', 'should not', 'cannot', 'may not', 'disallowed',
        'forbidden', 'prohibited', 'unacceptable'
    ]
    
    # Combine all patterns
    all_patterns = requirement_keywords + prohibition_patterns
    
    lines = text.split('\n')
    
    # Track the current document reference
    current_doc_ref = "Unknown"
    
    for i, line in enumerate(lines):
        # Update document reference when found
        if "[Document:" in line:
            current_doc_ref = line.strip()
            continue
            
        line_lower = line.lower()
        
        # Skip lines that are too short or likely headers
        if len(line.strip()) < 10 or (line.strip().endswith(':') and len(line.strip()) < 30):
            continue
            
        # Skip empty lines
        if not line.strip():
            continue
        
        # Check if line contains any of the requirement patterns
        if any(pattern in line_lower for pattern in all_patterns):
            # If reference wasn't found in the line, use the tracked reference
            doc_ref = current_doc_ref
            
            # Extract sentences that contain requirements
            # This helps to isolate just the requirement part of longer paragraphs
            sentences = re.split(r'(?<=[.!?])\s+', line)
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(pattern in sentence_lower for pattern in all_patterns):
                    requirements.append({
                        "text": sentence.strip(),
                        "reference": doc_ref
                    })
        
        # Also check the full paragraph for requirements
        # This captures requirements that span multiple lines
        if i > 0 and i < len(lines) - 1:
            paragraph = lines[i-1] + " " + line + " " + lines[i+1]
            paragraph_lower = paragraph.lower()
            
            # If paragraph contains requirement keywords but the line itself didn't match
            if not any(pattern in line_lower for pattern in all_patterns) and any(pattern in paragraph_lower for pattern in all_patterns):
                requirements.append({
                    "text": line.strip(),
                    "reference": current_doc_ref,
                    "context": "Extracted from paragraph context"
                })
    
    # Deduplicate requirements by checking for similar text
    unique_requirements = []
    for req in requirements:
        is_duplicate = False
        for unique in unique_requirements:
            # Simple similarity check - if 80% of words match, consider it a duplicate
            req_words = set(req["text"].lower().split())
            unique_words = set(unique["text"].lower().split())
            
            if req_words and unique_words:  # Ensure non-empty sets
                # Calculate similarity
                intersection = req_words.intersection(unique_words)
                union = req_words.union(unique_words)
                similarity = len(intersection) / len(union)
                
                if similarity > 0.8:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_requirements.append(req)
    
    return unique_requirements

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
    
    # Also write the output in the expected format for the task output
    task_output_file = output_dir / "extract_conditions_task_output.md"
    with open(task_output_file, "w", encoding="utf-8") as f:
        f.write("# Policy Compliance Conditions\n\n")
        for req in all_requirements:
            f.write(f"### {req['id']}\n\n")
            f.write(f"**Description:** {req['description']}\n\n")
            f.write(f"**Reference:** {req['reference']}\n\n")
            f.write("---\n\n")
    
    logger.info(f"Extracted {len(all_requirements)} policy conditions")
    logger.info(f"Results written to {output_file} and {task_output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())