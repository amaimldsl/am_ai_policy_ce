#!/usr/bin/env python3
"""
Script to parse conditions and generate conditions for the first task.
This script can be used if the crew fails to extract conditions properly.
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
    preprocessed_dir = Path(__file__).resolve().parent / "preprocessed"
    preprocessed_dir.mkdir(exist_ok=True)
    return preprocessed_dir

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

def extract_conditions_from_chunk(chunk_path):
    """Extract policy conditions from a single chunk - ENHANCED VERSION"""
    conditions = []
    
    try:
        with open(chunk_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Extract document name from chunk filename
        doc_name = chunk_path.name
        
        # Find document references in the text
        doc_refs = re.findall(r'\[Document: ([^,]+), Page (\d+)\]', text)
        doc_ref = f"{doc_refs[0][0]}, Page {doc_refs[0][1]}" if doc_refs else doc_name
        
        # Expanded keywords that indicate requirements
        req_keywords = [
            "shall", "must", "should", "required", "obligated", "necessary", 
            "mandatory", "comply", "compliance", "adhere", "ensure", "maintain", 
            "establish", "implement", "provide", "responsible", "accountable",
            "follow", "conduct", "perform", "review", "verify", "document",
            "record", "report", "complete", "submit", "authorize", "approve"
        ]
        
        # Prohibition keywords
        prohibition_keywords = [
            "prohibited", "shall not", "must not", "should not", "cannot", 
            "may not", "disallowed", "forbidden", "unacceptable", "not allowed", 
            "not permitted"
        ]
        
        # Combine keywords
        all_keywords = req_keywords + prohibition_keywords
        
        # Split text into lines and look for requirements
        lines = text.split("\n")
        current_doc_ref = doc_ref
        
        for i, line in enumerate(lines):
            # Update document reference when found
            if "[Document:" in line:
                page_match = re.search(r'\[Document: ([^,]+), Page (\d+)\]', line)
                if page_match:
                    current_doc_ref = f"{page_match.group(1)}, Page {page_match.group(2)}"
                continue
            
            line_lower = line.lower()
            
            # Skip lines that are too short or likely headers
            if len(line.strip()) < 10 or (line.strip().endswith(':') and len(line.strip()) < 30):
                continue
                
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check if line contains any of the requirement patterns
            if any(keyword in line_lower for keyword in all_keywords):
                # Try to get more context from surrounding lines (better context)
                start = max(0, i-2)  # Extended to 2 lines for better context
                end = min(len(lines), i+3)  # Extended to 2 lines after
                context = "\n".join(lines[start:end])
                
                # Try to extract specific sentences with requirements
                sentences = re.split(r'(?<=[.!?])\s+', line)
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in all_keywords) and len(sentence.strip()) > 10:
                        conditions.append({
                            "text": sentence.strip(),
                            "reference": current_doc_ref,
                            "context": context
                        })
                
                # If we didn't find specific sentences, use the whole line
                if not any(condition["text"] == sentence.strip() for sentence in sentences for condition in conditions):
                    conditions.append({
                        "text": line.strip(),
                        "reference": current_doc_ref,
                        "context": context
                    })
        
        # Add check for multi-line requirements by scanning consecutive lines
        for i in range(len(lines) - 1):
            current_line = lines[i].lower()
            next_line = lines[i+1].lower()
            
            # If current line ends with an incomplete phrase and next line starts with a requirement keyword
            if (current_line.endswith(',') or current_line.endswith(' and') or current_line.endswith(' or')) and \
               any(keyword in next_line for keyword in all_keywords):
                combined_line = lines[i] + " " + lines[i+1]
                start = max(0, i-1)
                end = min(len(lines), i+3)
                context = "\n".join(lines[start:end])
                
                # Extract document reference
                ref_found = False
                for j in range(max(0, i-5), i+1):
                    if j < len(lines) and "[Document:" in lines[j]:
                        page_match = re.search(r'\[Document: ([^,]+), Page (\d+)\]', lines[j])
                        if page_match:
                            current_doc_ref = f"{page_match.group(1)}, Page {page_match.group(2)}"
                            ref_found = True
                            break
                
                if not ref_found:
                    current_doc_ref = doc_ref
                
                conditions.append({
                    "text": combined_line.strip(),
                    "reference": current_doc_ref,
                    "context": context
                })
    
    except Exception as e:
        logger.error(f"Error processing {chunk_path}: {str(e)}")
    
    # Deduplicate conditions
    unique_conditions = []
    for condition in conditions:
        is_duplicate = False
        for unique in unique_conditions:
            # Simple similarity check - if 80% of words match, consider it a duplicate
            condition_words = set(condition["text"].lower().split())
            unique_words = set(unique["text"].lower().split())
            
            if condition_words and unique_words:  # Ensure non-empty sets
                # Calculate Jaccard similarity
                intersection = condition_words.intersection(unique_words)
                union = condition_words.union(unique_words)
                similarity = len(intersection) / len(union)
                
                if similarity > 0.8:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_conditions.append(condition)
    
    return unique_conditions

def main():
    """Main function to parse policy conditions"""
    preprocessed_dir = find_preprocessed_directory()
    output_dir = find_output_directory()
    
    # Check if preprocessed directory exists and has chunks
    chunks = list(preprocessed_dir.glob("*.txt"))
    if not chunks:
        logger.error("No preprocessed chunks found. Please run document_processor.py first.")
        return 1
    
    logger.info(f"Found {len(chunks)} chunks")
    
    # Process chunks
    all_conditions = []
    condition_counter = 1
    
    for chunk in chunks:
        logger.info(f"Processing {chunk}")
        conditions = extract_conditions_from_chunk(chunk)
        logger.info(f"  Found {len(conditions)} conditions")
        
        for condition in conditions:
            # Add to master list with ID
            condition["id"] = f"C-{condition_counter}"
            all_conditions.append(condition)
            condition_counter += 1
    
    # Remove duplicates by comparing text similarity
    unique_conditions = []
    for condition in all_conditions:
        is_duplicate = False
        for unique in unique_conditions:
            # Simple similarity check - if 80% of words match, consider it a duplicate
            condition_words = set(condition["text"].lower().split())
            unique_words = set(unique["text"].lower().split())
            
            if len(condition_words) > 0 and len(unique_words) > 0:
                # Calculate Jaccard similarity
                intersection = condition_words.intersection(unique_words)
                union = condition_words.union(unique_words)
                similarity = len(intersection) / len(union)
                
                if similarity > 0.8:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_conditions.append(condition)
    
    logger.info(f"Found {len(all_conditions)} total conditions, {len(unique_conditions)} unique conditions")
    
    # Generate markdown file with all unique conditions
    output_file = output_dir / "extract_conditions_task_output.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Policy Compliance Conditions\n\n")
        
        for condition in unique_conditions:
            f.write(f"### {condition['id']}\n\n")
            f.write(f"**Description:** {condition['text']}\n\n")
            f.write(f"**Reference:** {condition['reference']}\n\n")
            f.write("---\n\n")
    
    logger.info(f"Wrote {len(unique_conditions)} conditions to {output_file}")
    
    # Also generate a structured format for the next task
    structured_file = output_dir / "structured_conditions.md"
    with open(structured_file, "w", encoding="utf-8") as f:
        for condition in unique_conditions:
            f.write(f"{condition['id']}: {condition['text']} [{condition['reference']}]\n")
    
    logger.info(f"Wrote structured format to {structured_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())