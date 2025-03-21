#!/usr/bin/env python3
"""
Script to fix truncated or incomplete sentences in a compliance report.
This can be run as a standalone tool to improve report quality.
"""

import os
import sys
import re
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

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

def process_report(file_path):
    """
    Process a compliance report to fix incomplete sentences.
    
    Args:
        file_path (str): Path to the report file
        
    Returns:
        str: The processed report with all sentences completed
    """
    try:
        # Read the report
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split the report into sections based on Markdown headers
        sections = []
        current_section = []
        
        for line in content.split('\n'):
            if line.startswith('#'):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
                current_section.append(line)
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        # Process each section
        processed_sections = []
        for section in sections:
            processed_sections.append(process_section(section))
        
        # Combine processed sections
        return '\n\n'.join(processed_sections)
        
    except Exception as e:
        print(f"Error processing report: {str(e)}")
        return None


def process_section(text):
    """
    Process a section of the report to identify and fix incomplete sentences.
    
    Args:
        text (str): The section text to process
        
    Returns:
        str: The processed text with completed sentences
    """
    # Skip empty text
    if not text.strip():
        return text
        
    # Split text into paragraphs and handle each one
    paragraphs = re.split(r'\n\s*\n', text)
    processed_paragraphs = []
    
    for paragraph in paragraphs:
        # Skip special formatting (code blocks, tables, lists)
        if paragraph.strip().startswith('```') or '|' in paragraph or paragraph.strip().startswith('#'):
            processed_paragraphs.append(paragraph)
            continue
            
        # Process bullet points separately (don't modify the bullet format)
        if re.match(r'^\s*[-*•]|\d+\.\s+', paragraph):
            lines = paragraph.split('\n')
            for i, line in enumerate(lines):
                # Only fix the content after the bullet
                bullet_match = re.match(r'^(\s*[-*•]|\s*\d+\.\s+)(.*)', line)
                if bullet_match:
                    bullet = bullet_match.group(1)
                    content = bullet_match.group(2)
                    
                    # Check if content is incomplete
                    if content and not any(content.strip().endswith(c) for c in ['.', '!', '?', ':', ';']):
                        lines[i] = bullet + complete_truncated_sentence(content)
            
            processed_paragraphs.append('\n'.join(lines))
            continue
        
        # Handle attribute lines (**Key:** Value)
        lines = paragraph.split('\n')
        for i, line in enumerate(lines):
            # Check for attribute format
            attr_match = re.match(r'^(\s*\*\*[^:]+:\*\*\s*)(.*)', line)
            if attr_match:
                prefix = attr_match.group(1)
                content = attr_match.group(2).strip()
                
                # Complete content if needed
                if content and not any(content.endswith(c) for c in ['.', '!', '?', ':', ';']):
                    lines[i] = prefix + complete_truncated_sentence(content)
            # Regular text line
            elif line.strip() and not line.startswith('#'):
                # Check if the line is incomplete
                if not any(line.strip().endswith(c) for c in ['.', '!', '?', ':', ';']):
                    lines[i] = complete_truncated_sentence(line)
        
        processed_paragraphs.append('\n'.join(lines))
    
    return '\n\n'.join(processed_paragraphs)

def complete_truncated_sentence(text):
    """
    Complete truncated sentences with meaningful endings
    based on context and common compliance language patterns.
    """
    # Already complete sentence
    if any(text.endswith(c) for c in ['.', '!', '?']):
        return text
    
    # Handle sentences ending with colons and semicolons
    if text.endswith((':',';')):
        return text
    
    text = text.strip()
    text_lower = text.lower()
    
    # Check for common truncated endings and provide appropriate completions
    
    # Modal verbs without a following action
    modal_patterns = [
        (r'(shall|must|should|will|is required to|are required to)\s*$', 
         " be implemented in accordance with policy requirements."),
        (r'(shall|must|should|will|is required to|are required to)\s+(be|have)\s*$', 
         " properly documented and maintained."),
        (r'(shall|must|should|will|is required to|are required to)\s+(not)\s*$', 
         " be permitted without proper authorization."),
    ]
    
    for pattern, completion in modal_patterns:
        if re.search(pattern, text):
            return text + completion
    
    # Conjunctions
    conjunction_completions = {
        'and': " follow all applicable compliance requirements.",
        'or': " meet alternative compliance criteria as specified in the policy.",
        'but': " exceptions must be documented and approved.",
        'which': " must be properly documented.",
        'that': " is specified in the relevant policies and procedures.",
        'where': " specified in the applicable standards."
    }
    
    for conjunction, completion in conjunction_completions.items():
        if text_lower.endswith(conjunction):
            return text + completion
    
    # Prepositions
    preposition_completions = {
        'to': " the required standards and specifications.",
        'with': " the appropriate authorization and documentation.",
        'by': " authorized personnel according to established procedures.",
        'for': " compliance with relevant regulations and standards.",
        'in': " accordance with established policies and procedures.",
        'on': " a regular basis as required by policy.",
        'at': " intervals specified in the compliance framework."
    }