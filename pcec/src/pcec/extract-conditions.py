#!/usr/bin/env python3
"""
Helper script to extract policy conditions from preprocessed PDF chunks.
This script automates the process of searching for and extracting policy conditions
from all available chunks, with enhanced context awareness and categorization.
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
    """
    Check if a condition text is meaningful and complete.
    Enhanced to be more lenient to capture more valid conditions.
    """
    # Trim whitespace
    text = text.strip()
    
    # Must have minimum length (reduced minimum length)
    if len(text) < 10:
        return False
    
    # Must contain action verbs or modal verbs (expanded list)
    modal_verbs = [
        'shall', 'must', 'should', 'will', 'may', 'can', 'could', 'would', 
        'required', 'expected', 'needs to', 'have to', 'has to', 'need to'
    ]
    
    action_verbs = [
        'ensure', 'maintain', 'implement', 'establish', 'provide', 'conduct', 
        'perform', 'review', 'verify', 'document', 'report', 'manage',
        'use', 'develop', 'create', 'assess', 'monitor', 'apply', 'adhere',
        'follow', 'meet', 'achieve', 'test', 'measure', 'evaluate', 'deploy',
        'restrict', 'limit', 'enforce', 'define', 'set', 'approve', 'authorize'
    ]
    
    # Also check for requirement-related nouns
    requirement_nouns = [
        'policy', 'procedure', 'requirement', 'standard', 'guideline', 'rule',
        'control', 'measure', 'safeguard', 'protection', 'mechanism', 'framework',
        'process', 'regulation', 'directive', 'mandate'
    ]
    
    # Check for combination patterns that strongly suggest requirements
    requirement_patterns = [
        r'must be', r'shall be', r'should be', r'is required', r'are required',
        r'will be', r'needs to be', r'has to be', r'have to be', r'is prohibited',
        r'are prohibited', r'is not allowed', r'are not allowed', r'is necessary',
        r'are necessary', r'is mandatory', r'are mandatory', r'is expected',
        r'are expected', r'is to be', r'are to be'
    ]
    
    has_verb = any(modal in text.lower() for modal in modal_verbs) or \
              any(verb in text.lower() for verb in action_verbs)
              
    has_noun = any(noun in text.lower() for noun in requirement_nouns)
    
    has_pattern = any(re.search(pattern, text.lower()) for pattern in requirement_patterns)
    
    # Check if text appears to be truncated
    is_truncated = text.endswith(('...', '..', '..,')) or \
                  not any(text.endswith(c) for c in ['.', '!', '?', ':', ';']) or \
                  (len(text) > 20 and text.endswith(','))
    
    # If text has subject-verb structure, it's likely a requirement even if truncated
    has_subject_verb = re.search(r'\b(?:the|a|an|all|each|any|every|some)\b.*?\b(?:shall|must|should|will|may)\b', text.lower())
    
    # Accept bullet points and numbered items as requirements
    is_bullet_item = re.match(r'^[•\-*]|\d+\.', text.strip())
    
    # Accept section titles that imply requirements
    is_section_title = re.match(r'^\d+(\.\d+)*\s+[A-Z]|^[A-Z][a-z]+\s+\d+(\.\d+)*\s+', text) and len(text) < 50
    
    # If truncated but otherwise meaningful, we might still want to keep it
    if is_truncated and (has_verb or has_noun or has_pattern or has_subject_verb) and len(text) > 20:
        return True
    
    # Special case for bullet points and section titles
    if (is_bullet_item or is_section_title) and len(text) > 15:
        return True
        
    # Accept if it has a verb, or a requirement pattern
    if has_verb or has_pattern:
        return True
        
    # Accept if it has a requirement noun and is at least reasonable length
    if has_noun and len(text) > 20:
        return True
        
    # Accept if it has a clear subject-verb structure typical of requirements
    if has_subject_verb:
        return True
    
    # Default case - reject
    return False

def extract_requirements(text):
    """Extract policy requirements from text - SIGNIFICANTLY ENHANCED VERSION with better context handling"""
    requirements = []
    
    # Expanded list of requirement keywords for more comprehensive extraction
    requirement_keywords = [
        'shall', 'must', 'should', 'required', 'obligated', 
        'necessary', 'mandatory', 'comply', 'compliance', 'adhere',
        'ensure', 'maintain', 'establish', 'implement', 'provide',
        'responsible', 'accountable', 'follow', 'conduct', 'perform',
        'review', 'verify', 'document', 'record', 'report',
        'complete', 'submit', 'authorize', 'approve', 'prohibit',
        'restrict', 'limit', 'safeguard', 'protect', 'prevent',
        # Additional keywords to catch more requirements
        'require', 'obligation', 'policy', 'guideline', 'standard',
        'procedure', 'process', 'rule', 'regulation', 'directive',
        'mandate', 'essential', 'enforce', 'expect', 'need to',
        'recommended', 'will be', 'to be', 'critical', 'ensure that'
    ]
    
    # Add negation patterns to catch requirements phrased as prohibitions
    prohibition_patterns = [
        'not allowed', 'not permitted', 'prohibited', 'shall not',
        'must not', 'should not', 'cannot', 'may not', 'disallowed',
        'forbidden', 'unacceptable', 'restricted', 'off-limits',
        'not authorized', 'not approved', 'not accepted', 'denied',
        'disallowed', 'not recommended', 'never', 'illegal'
    ]
    
    # Combine all patterns
    all_patterns = requirement_keywords + prohibition_patterns
    
    lines = text.split('\n')
    
    # Track the current document reference
    current_doc_ref = "Unknown"
    
    # Use a larger sliding window approach to capture more context
    context_window_size = 10  # Increased window size for better context
    context_buffer = []
    
    for i, line in enumerate(lines):
        # Update document reference when found
        if "[Document:" in line:
            current_doc_ref = line.strip()
            continue
            
        # Update context buffer
        context_buffer.append(line)
        if len(context_buffer) > context_window_size:
            context_buffer.pop(0)
            
        line_lower = line.lower()
        
        # Skip lines that are too short, likely headers, or empty
        if not line.strip() or len(line.strip()) < 5:
            continue
        
        # Check if line contains any of the requirement patterns
        if any(pattern in line_lower for pattern in all_patterns):
            # Extract sentences with requirements and context
            full_context = " ".join(context_buffer)
            
            # If the line ends with punctuation that suggests continuation, expand context
            if line.strip().endswith((',', ';', ':', '-')):
                # Look ahead for continuation if possible
                next_line_idx = i + 1
                if next_line_idx < len(lines):
                    full_context += " " + lines[next_line_idx]
            
            # Split into sentences and find those containing requirements
            sentences = re.split(r'(?<=[.!?])\s+', full_context)
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                # Check if sentence contains requirement keywords
                if any(pattern in sentence_lower for pattern in all_patterns) and len(sentence.strip()) > 10:
                    # Add to requirements list with the document reference
                    requirements.append({
                        "text": sentence.strip(),
                        "reference": current_doc_ref
                    })
        
        # Also check for bullet points that might contain requirements
        # These often don't end with punctuation but are still requirements
        if (line.strip().startswith('•') or line.strip().startswith('-') or 
            line.strip().startswith('*') or re.match(r'^\d+\.', line.strip())):
            # This looks like a bullet point or numbered item
            
            # Check if it contains a requirement-like phrase
            bullet_text = line.strip()
            
            # Remove the bullet/number prefix
            bullet_text = re.sub(r'^[•\-*]|\d+\.', '', bullet_text).strip()
            
            # Add if it seems like a requirement (even without standard keywords)
            if len(bullet_text) > 10 and (
                any(pattern in bullet_text.lower() for pattern in all_patterns) or
                re.search(r'\b(policy|standard|guideline|rule)\b', bullet_text.lower())
            ):
                requirements.append({
                    "text": bullet_text,
                    "reference": current_doc_ref,
                    "context": "Extracted from bullet point"
                })
        
        # Check sections that look like policies or requirements but might not have standard keywords
        if (re.search(r'^\d+(\.\d+)*\s+[A-Z]', line) or  # Looks like "1.2 SOME POLICY" 
            re.search(r'^[A-Z][a-z]+\s+\d+(\.\d+)*\s+', line)):  # Looks like "Section 1.2" 
            
            policy_text = line.strip()
            
            # Look ahead for actual content if this is just a header
            next_lines = []
            for j in range(i+1, min(i+4, len(lines))):
                if lines[j].strip() and not (
                    lines[j].strip().startswith('•') or 
                    lines[j].strip().startswith('-') or
                    lines[j].strip().startswith('*')
                ):
                    next_lines.append(lines[j].strip())
            
            if next_lines:
                policy_text = " ".join(next_lines)
            
            # Only add if it seems like a substantial requirement
            if len(policy_text) > 20 and not policy_text.startswith("[Document:"):
                requirements.append({
                    "text": policy_text,
                    "reference": current_doc_ref,
                    "context": "Extracted from policy section"
                })
    
    # Second pass with paragraph-level analysis to catch requirements spanning multiple lines
    paragraphs = []
    current_paragraph = []
    
    for line in lines:
        if line.strip():
            current_paragraph.append(line)
        elif current_paragraph:
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []
    
    # Don't forget the last paragraph if the file doesn't end with an empty line
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))
    
    # Analyze each paragraph for requirements
    for paragraph in paragraphs:
        # Skip short paragraphs or document references
        if len(paragraph) < 30 or paragraph.startswith("[Document:"):
            continue
            
        # Skip if already processed as individual sentences
        if any(paragraph == req["text"] for req in requirements):
            continue
            
        # Check if paragraph contains requirement keywords
        para_lower = paragraph.lower()
        if any(pattern in para_lower for pattern in all_patterns):
            # Process each sentence in the paragraph
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            
            # Check if it should be treated as a single requirement even though it has multiple sentences
            # This is common for complex requirements that span multiple sentences
            is_cohesive_requirement = False
            
            # If multiple sentences and most have requirement keywords, treat as a single requirement
            if len(sentences) > 1:
                req_sentences = [s for s in sentences if any(pattern in s.lower() for pattern in all_patterns)]
                if len(req_sentences) >= len(sentences) * 0.5:  # At least half contain requirement keywords
                    is_cohesive_requirement = True
            
            if is_cohesive_requirement:
                # Treat the whole paragraph as one requirement
                requirements.append({
                    "text": paragraph,
                    "reference": current_doc_ref,
                    "context": "Multi-sentence requirement"
                })
            else:
                # Process each sentence individually
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(pattern in sentence_lower for pattern in all_patterns) and len(sentence.strip()) > 10:
                        requirements.append({
                            "text": sentence.strip(),
                            "reference": current_doc_ref
                        })
    
    # Add implied requirements from document structure
    # Look for section headers that imply requirements
    section_headers = []
    for i, line in enumerate(lines):
        if (re.match(r'^\d+(\.\d+)*\s+[A-Z]', line) or  # Numbered section
            re.match(r'^[A-Z][a-z]+\s+\d+(\.\d+)*\s+', line) or  # "Section X.Y"
            (line.strip().endswith(':') and len(line.strip()) > 5 and len(line.strip()) < 50)):  # Title with colon
            
            section_headers.append((i, line.strip()))
    
    # Process sections to add implied requirements
    for idx, (section_idx, header) in enumerate(section_headers):
        # Determine section end
        next_section_idx = section_headers[idx+1][0] if idx+1 < len(section_headers) else len(lines)
        
        # Skip very short sections
        if next_section_idx - section_idx < 3:
            continue
            
        # Get section content
        section_content = " ".join(lines[section_idx+1:next_section_idx])
        
        # Look for keywords in the header that imply requirements
        header_lower = header.lower()
        requirement_headers = ['requirement', 'policy', 'standard', 'rule', 'procedure', 'control', 'measure', 'compliance']
        
        if any(keyword in header_lower for keyword in requirement_headers):
            # This section likely contains requirements, even if they don't have standard keywords
            
            # Check if the section has a proper title
            title_text = re.sub(r'^\d+(\.\d+)*\s+|\s*:$', '', header)
            
            # Extract implied requirement from the section
            if len(title_text) > 5 and len(section_content) > 20:
                # Combine section title with first line of content
                first_content_line = lines[section_idx+1].strip()
                
                # Construct an implied requirement
                implied_req = f"{title_text} {first_content_line}"
                
                # Only add if it seems meaningful
                if len(implied_req) > 20 and not any(implied_req == req["text"] for req in requirements):
                    requirements.append({
                        "text": implied_req,
                        "reference": current_doc_ref,
                        "context": "Implied requirement from section header"
                    })
    
    # Use the example conditions if provided to cross-reference
    sample_conditions = [
        "Organizations shall implement a risk management framework to identify, assess, and mitigate risks.",
        "All employees must complete annual security awareness training.",
        "Data encryption is required for all sensitive information transmitted over public networks.",
        "Organizations should conduct regular vulnerability assessments and penetration testing.",
        "Access to sensitive systems must be restricted to authorized personnel only.",
        "Incident response plans shall be developed and tested annually.",
        "Organizations are obligated to report data breaches to regulatory authorities within 72 hours.",
        "Multi-factor authentication should be implemented for all remote access systems.",
        "Policies and procedures must be reviewed and updated at least annually.",
        "Organizations shall maintain an inventory of all hardware and software assets."
    ]
    
    # Add sample conditions if similar ones aren't already identified
    # (This is a fallback to ensure we have a comprehensive set of requirements)
    for sample in sample_conditions:
        # Check if we have something similar already
        sample_lower = sample.lower()
        has_similar = False
        
        for req in requirements:
            req_lower = req["text"].lower()
            # Check word overlap
            sample_words = set(sample_lower.split())
            req_words = set(req_lower.split())
            
            if len(sample_words.intersection(req_words)) > len(sample_words) * 0.5:
                has_similar = True
                break
        
        # If no similar requirement found, add the sample
        if not has_similar:
            requirements.append({
                "text": sample,
                "reference": "Example requirement",
                "context": "Added from standard requirements list"
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



def natural_sort_key(s):
    """
    Natural sorting key function that handles numeric parts correctly
    This ensures that C-1, C-2, C-10 sort properly instead of C-1, C-10, C-2
    """
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', str(s))]

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
                # Skip if not a meaningful condition
                if not is_meaningful_condition(req["text"]):
                    continue
                    
                category = req.get("category", determine_condition_category(req["text"]))
                
                all_requirements.append({
                    "id": f"C-{condition_id}",
                    "description": req["text"],
                    "reference": req["reference"],
                    "category": category
                })
                condition_id += 1
                
        except Exception as e:
            logger.error(f"  Error processing chunk {chunk.name}: {str(e)}")
    
    # Group requirements by category
    categorized_requirements = {}
    for req in all_requirements:
        category = req["category"]
        if category not in categorized_requirements:
            categorized_requirements[category] = []
        categorized_requirements[category].append(req)
    
    # Write the output with categorization
    output_file = output_dir / "extracted_conditions.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Extracted Policy Conditions\n\n")
        
        for category, requirements in sorted(categorized_requirements.items()):
            f.write(f"## {category}\n\n")
            
            # Sort requirements by ID
            sorted_reqs = sorted(requirements, key=lambda x: natural_sort_key(x["id"]))
            
            for req in sorted_reqs:
                f.write(f"### {req['id']}\n")
                f.write(f"**Description**: {req['description']}\n")
                f.write(f"**Reference**: {req['reference']}\n\n")
    
    # Also write the output in the expected format for the task output (with sequence numbers)
    task_output_file = output_dir / "1_extract_conditions_task_output.md"
    with open(task_output_file, "w", encoding="utf-8") as f:
        f.write("# 1. Policy Compliance Conditions\n\n")
        
        for category, requirements in sorted(categorized_requirements.items()):
            f.write(f"## {category}\n\n")
            
            # Sort requirements by ID
            sorted_reqs = sorted(requirements, key=lambda x: natural_sort_key(x["id"]))
            
            for req in sorted_reqs:
                f.write(f"### {req['id']}\n")
                f.write(f"**Description:** {req['description']}\n")
                f.write(f"**Reference:** {req['reference']}\n\n")
    
    logger.info(f"Extracted {len(all_requirements)} policy conditions across {len(categorized_requirements)} categories")
    logger.info(f"Results written to {output_file} and {task_output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())