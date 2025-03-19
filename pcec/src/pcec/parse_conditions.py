#!/usr/bin/env python3
"""
Script to parse conditions and generate conditions for the first task.
This script can be used if the crew fails to extract conditions properly.
Enhanced with categorization and improved context extraction.
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

def determine_condition_category(description):
    """Determine the category of a condition based on its description"""
    description_lower = description.lower()
    
    # Define category keywords
    categories = {
        "Access Management": ["access", "authentication", "authorization", "login", "credential", "password"],
        "Data Protection": ["data", "information", "confidential", "encrypt", "sensitive", "store", "backup"],
        "Security": ["security", "cybersecurity", "protection", "vulnerability", "threat", "malware", "attack"],
        "Compliance": ["compliance", "regulatory", "regulation", "law", "requirement", "standard", "guideline"],
        "Training": ["training", "awareness", "education", "instruct", "teach", "learn", "knowledge"],
        "Monitoring": ["monitor", "surveillance", "detect", "alert", "observe", "track", "log"],
        "Reporting": ["report", "document", "record", "communication", "notify", "inform"],
        "Incident Management": ["incident", "event", "breach", "violation", "issue", "problem", "response"],
        "Physical Security": ["physical", "facility", "premise", "building", "location", "site", "area"],
        "Governance": ["governance", "policy", "procedure", "management", "oversight", "responsibility"]
    }
    
    # Find matching categories
    matched_categories = []
    for category, keywords in categories.items():
        if any(keyword in description_lower for keyword in keywords):
            matched_categories.append(category)
    
    # If multiple matches, choose the one with the most keyword matches
    if len(matched_categories) > 1:
        category_counts = {}
        for category in matched_categories:
            count = sum(1 for keyword in categories[category] if keyword in description_lower)
            category_counts[category] = count
        
        # Return the category with the highest count
        return max(category_counts.items(), key=lambda x: x[1])[0]
    
    # Return the matched category or default
    return matched_categories[0] if matched_categories else "General Requirements"

def is_meaningful_condition(text):
    """Check if a condition text is meaningful and complete"""
    # Trim whitespace
    text = text.strip()
    
    # Must have minimum length
    if len(text) < 15:
        return False
    
    # Must contain action verbs or modal verbs
    modal_verbs = ['shall', 'must', 'should', 'will', 'may', 'can', 'could', 'would']
    action_verbs = ['ensure', 'maintain', 'implement', 'establish', 'provide', 'conduct', 
                    'perform', 'review', 'verify', 'document', 'report', 'manage']
    
    has_verb = any(modal in text.lower() for modal in modal_verbs) or \
              any(verb in text.lower() for verb in action_verbs)
    
    # Check if text appears to be truncated
    is_truncated = text.endswith(('...', '..',)) or \
                   not any(text.endswith(c) for c in ['.', '!', '?', ':', ';'])
    
    # If truncated but otherwise meaningful, we might still want to keep it
    if is_truncated and has_verb and len(text) > 50:
        return True
        
    # Complete sentence and has verbs
    return has_verb and not is_truncated

def extract_conditions_from_chunk(chunk_path):
    """Extract policy conditions from a single chunk - ENHANCED VERSION with categorization"""
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
        
        # Use a sliding window approach to capture more context
        context_window_size = 7  # Increased window size for better context
        context_buffer = []
        
        for i, line in enumerate(lines):
            # Update document reference when found
            if "[Document:" in line:
                page_match = re.search(r'\[Document: ([^,]+), Page (\d+)\]', line)
                if page_match:
                    current_doc_ref = f"{page_match.group(1)}, Page {page_match.group(2)}"
                continue
            
            # Update context buffer
            context_buffer.append(line)
            if len(context_buffer) > context_window_size:
                context_buffer.pop(0)
                
            line_lower = line.lower()
            
            # Skip lines that are too short, likely headers, or empty
            if len(line.strip()) < 10 or (line.strip().endswith(':') and len(line.strip()) < 30) or not line.strip():
                continue
            
            # Check if line contains any of the requirement patterns
            if any(keyword in line_lower for keyword in all_keywords):
                # Get context from buffer
                context = "\n".join(context_buffer)
                
                # Try to extract specific sentences with requirements
                sentences = re.split(r'(?<=[.!?])\s+', context)
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in all_keywords):
                        if is_meaningful_condition(sentence):
                            # Determine category
                            category = determine_condition_category(sentence)
                            
                            conditions.append({
                                "text": sentence.strip(),
                                "reference": current_doc_ref,
                                "context": context,
                                "category": category
                            })
                
                # If we didn't find specific sentences, use the whole line
                if not any(condition["text"] == sentence.strip() for sentence in sentences for condition in conditions):
                    if is_meaningful_condition(line):
                        # Determine category
                        category = determine_condition_category(line)
                        
                        conditions.append({
                            "text": line.strip(),
                            "reference": current_doc_ref,
                            "context": context,
                            "category": category
                        })
        
        # Add check for multi-line requirements by scanning consecutive lines
        for i in range(len(lines) - 1):
            current_line = lines[i].lower()
            next_line = lines[i+1].lower()
            
            # If current line ends with an incomplete phrase and next line starts with a requirement keyword
            if (current_line.endswith(',') or current_line.endswith(' and') or current_line.endswith(' or')) and \
               any(keyword in next_line for keyword in all_keywords):
                combined_line = lines[i] + " " + lines[i+1]
                
                if is_meaningful_condition(combined_line):
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
                    
                    # Determine category
                    category = determine_condition_category(combined_line)
                    
                    conditions.append({
                        "text": combined_line.strip(),
                        "reference": current_doc_ref,
                        "context": context,
                        "category": category
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

def natural_sort_key(s):
    """
    Natural sorting key function that handles numeric parts correctly
    This ensures that C-1, C-2, C-10 sort properly instead of C-1, C-10, C-2
    """
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', str(s))]

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
            # Skip if not meaningful
            if not is_meaningful_condition(condition["text"]):
                continue
                
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
    
    # Group conditions by category
    categorized_conditions = {}
    for condition in unique_conditions:
        category = condition.get("category", "General Requirements")
        if category not in categorized_conditions:
            categorized_conditions[category] = []
        categorized_conditions[category].append(condition)
    
    # Generate markdown file with all unique conditions
    output_file = output_dir / "1_extract_conditions_task_output.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 1. Policy Compliance Conditions\n\n")
        
        for category, conditions in sorted(categorized_conditions.items()):
            f.write(f"## {category}\n\n")
            
            # Sort conditions by ID within category
            sorted_conditions = sorted(conditions, key=lambda x: natural_sort_key(x["id"]))
            
            for condition in sorted_conditions:
                f.write(f"### {condition['id']}\n\n")
                f.write(f"**Description:** {condition['text']}\n\n")
                f.write(f"**Reference:** {condition['reference']}\n\n")
    
    logger.info(f"Wrote {len(unique_conditions)} conditions across {len(categorized_conditions)} categories to {output_file}")
    
    # Also generate a structured format for the next task
    structured_file = output_dir / "structured_conditions.md"
    with open(structured_file, "w", encoding="utf-8") as f:
        f.write("# Structured Policy Conditions\n\n")
        
        for category, conditions in sorted(categorized_conditions.items()):
            f.write(f"## {category}\n\n")
            
            # Sort conditions by ID within category
            sorted_conditions = sorted(conditions, key=lambda x: natural_sort_key(x["id"]))
            
            for condition in sorted_conditions:
                f.write(f"{condition['id']}: {condition['text']} [{condition['reference']}]\n\n")
    
    logger.info(f"Wrote structured format to {structured_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())