def verify_report_completeness(report_content):
    """
    Verify that all sentences in the report are complete and meaningful.
    Post-processes the report to fix any truncated or incomplete sentences.
    
    Args:
        report_content (str): The content of the report to verify
        
    Returns:
        str: The verified and fixed report content
    """
    # Split the report into sections (preserving markdown headers)
    sections = []
    current_section = []
    
    for line in report_content.split('\n'):
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
        # Preserve markdown headers and formatting
        if section.strip().startswith('#'):
            header_lines = []
            content_lines = []
            
            for line in section.split('\n'):
                if line.startswith('#') or line.startswith('|') or line.strip() == '':
                    header_lines.append(line)
                else:
                    content_lines.append(line)
            
            header = '\n'.join(header_lines)
            content = '\n'.join(content_lines)
            
            # Process the content text for sentence completeness
            processed_content = process_section_text(content)
            
            processed_sections.append(f"{header}\n{processed_content}")
        else:
            processed_content = process_section_text(section)
            processed_sections.append(processed_content)
    
    # Combine processed sections
    return '\n\n'.join(processed_sections)

def process_section_text(text):
    """
    Process the text of a report section to ensure all sentences are complete.
    
    Args:
        text (str): The text content to process
        
    Returns:
        str: The processed text with completed sentences
    """
    import re
    from tools.Parser_Utils import ParserUtils
    
    # Skip if empty
    if not text.strip():
        return text
    
    # Helper function to find sentence boundaries
    def find_sentence_boundaries(text):
        """Find the start and end positions of sentences in the text."""
        sentence_pattern = re.compile(r'((?:[^.!?]|\.(?=[a-z]))+[.!?])', re.DOTALL)
        sentences = []
        
        for match in sentence_pattern.finditer(text):
            sentences.append((match.start(), match.end(), match.group(1)))
        
        # Check for potential incomplete last sentence
        if sentences:
            last_end = sentences[-1][1]
            remaining_text = text[last_end:].strip()
            if remaining_text:
                sentences.append((last_end, len(text), remaining_text))
        elif text.strip():
            # The entire text might be one incomplete sentence
            sentences.append((0, len(text), text))
        
        return sentences
    
    # Process descriptive text (not code blocks, tables, or lists)
    # Detect markdown code blocks and preserve them
    code_block_pattern = re.compile(r'```(?:.*?)\n(.*?)```', re.DOTALL)
    code_blocks = {}
    
    # Replace code blocks with placeholders
    def replace_code_blocks(match):
        placeholder = f"CODE_BLOCK_{len(code_blocks)}"
        code_blocks[placeholder] = match.group(0)
        return placeholder
    
    text_with_placeholders = re.sub(code_block_pattern, replace_code_blocks, text)
    
    # Find all sentences in the text
    sentences = find_sentence_boundaries(text_with_placeholders)
    
    # Process each sentence
    updated_text = text_with_placeholders
    offset = 0  # Track offset due to text changes
    
    for start, end, sentence in sorted(sentences, key=lambda x: x[0], reverse=True):
        # Skip placeholder sentences
        if any(placeholder in sentence for placeholder in code_blocks):
            continue
        
        # Skip items in bullet lists, numbered lists, or table rows
        if re.match(r'^\s*[-*•]|\d+\.\s+', sentence) or '|' in sentence:
            continue
        
        # Handle attributes in markdown (e.g., **Description:** Some text)
        attribute_match = re.match(r'^\s*\*\*([^:]+):\*\*\s*(.*)', sentence)
        if attribute_match:
            attr_name = attribute_match.group(1)
            attr_value = attribute_match.group(2).strip()
            
            # Only process the attribute value if it's not empty
            if attr_value:
                # Check if the value is complete
                if not any(attr_value.endswith(c) for c in ['.', '!', '?', ':', ';']):
                    # Complete the value using ParserUtils
                    completed_value = ParserUtils.complete_truncated_sentence(attr_value)
                    
                    # Update the sentence with the completed value
                    new_sentence = f"**{attr_name}:** {completed_value}"
                    
                    # Replace in the text
                    updated_text = updated_text[:start+offset] + new_sentence + updated_text[end+offset:]
                    offset += len(new_sentence) - (end - start)
            
            continue
        
        # Check if the sentence is incomplete
        if not any(sentence.strip().endswith(c) for c in ['.', '!', '?', ':', ';']):
            # Complete the sentence using ParserUtils
            completed_sentence = ParserUtils.complete_truncated_sentence(sentence)
            
            # Replace the incomplete sentence with the completed one
            updated_text = updated_text[:start+offset] + completed_sentence + updated_text[end+offset:]
            offset += len(completed_sentence) - (end - start)
    
    # Restore code blocks
    for placeholder, code_block in code_blocks.items():
        updated_text = updated_text.replace(placeholder, code_block)
    
    return updated_text
