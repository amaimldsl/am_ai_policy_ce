# tools/Parser_Utils.py - Enhanced version
import re
from typing import List, Dict, Any, Set, Tuple
import logging
import functools

logger = logging.getLogger(__name__)

class ParserUtils:
    """
    Centralized parsing utilities to standardize data extraction and formatting
    across different tools and eliminate redundancy.
    """
    
    @staticmethod
    def natural_sort_key(s):
        """
        Natural sorting key function that handles numeric parts correctly
        This ensures that C-1, C-2, C-10 sort properly instead of C-1, C-10, C-2
        """
        return [int(text) if text.isdigit() else text.lower() 
                for text in re.split(r'(\d+)', str(s))]
    
    @staticmethod
    def determine_condition_category(description: str) -> str:
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
    
    @staticmethod
    def is_meaningful_condition(text: str) -> bool:
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
    #################################
    @staticmethod
    def parse_conditions(conditions_text: str) -> List[Dict[str, Any]]:
        """
        Parse condition text into a standardized structure.
        Works with multiple input formats. Enhanced to ensure meaningful conditions.
        """
        parsed = []
        
        try:
            # Primary pattern for condition extraction
            condition_patterns = [
                # Format: C-123: Description [Reference]
                re.compile(r'(C-\d+):\s*(.*?)(?:\s*\[([^]]+)\])?$', re.MULTILINE),
                
                # Format: ### C-123
                re.compile(r'###\s*(C-\d+)\s*\n\n\*\*Description:\*\*\s*(.*?)\n\n\*\*Reference:\*\*\s*(.*?)(?:\n\n|\Z)', re.DOTALL),
                
                # Format: ## C-123: Description
                re.compile(r'##\s*(C-\d+):\s*(.*?)(?:\n|$)', re.DOTALL),
                
                # Format: Condition ID: 123 - Description
                re.compile(r'Condition ID:\s*(\d+)\s*-\s*(.*?)(?:\n|$)', re.DOTALL)
            ]
            
            # Try each pattern
            for pattern in condition_patterns:
                matches = list(pattern.finditer(conditions_text))
                if matches:
                    for match in matches:
                        if len(match.groups()) >= 2:
                            # Handle condition ID variations
                            if match.group(1).startswith('C-'):
                                condition_id = match.group(1)
                            else:
                                condition_id = f"C-{match.group(1)}"
                                
                            description = match.group(2).strip()
                            reference = match.group(3) if len(match.groups()) > 2 and match.group(3) else ""
                            
                            # Skip if not a meaningful condition
                            if not ParserUtils.is_meaningful_condition(description):
                                continue
                                
                            # Determine category
                            category = ParserUtils.determine_condition_category(description)
                            
                            parsed.append({
                                "id": condition_id,
                                "description": description,
                                "reference": reference,
                                "category": category
                            })
                    break  # Stop if we found matches with this pattern
            
            # If no matches found with standard patterns, try the more detailed ### C-123 format
            if not parsed:
                detailed_pattern = re.compile(r'###\s*(C-\d+)\s*\n\n\*\*Description:\*\*\s*(.*?)\n\n\*\*Reference:\*\*\s*(.*?)(?:\n\n---|\Z)', re.DOTALL)
                matches = list(detailed_pattern.finditer(conditions_text))
                if matches:
                    for match in matches:
                        condition_id = match.group(1)
                        description = match.group(2).strip()
                        reference = match.group(3).strip()
                        
                        # Skip if not a meaningful condition
                        if not ParserUtils.is_meaningful_condition(description):
                            continue
                            
                        # Determine category
                        category = ParserUtils.determine_condition_category(description)
                        
                        parsed.append({
                            "id": condition_id,
                            "description": description,
                            "reference": reference,
                            "category": category
                        })
            
            # If still no matches found, try to extract from unstructured text
            if not parsed:
                # Look for lines with keywords that suggest requirements
                requirement_indicators = [
                    'shall', 'must', 'should', 'required', 'obligated', 'necessary',
                    'mandatory', 'comply', 'compliance', 'adhere', 'ensure', 'maintain',
                    'establish', 'implement', 'provide', 'responsible', 'accountable',
                    'follow', 'conduct', 'perform', 'review', 'verify', 'document',
                    'record', 'report', 'complete', 'submit', 'authorize', 'approve',
                    'prohibit', 'restrict', 'limit', 'safeguard', 'protect', 'prevent'
                ]
                lines = conditions_text.split('\n')
                
                # Track context for better extraction
                context_buffer = []
                current_doc_ref = "Unknown"
                
                for i, line in enumerate(lines):
                    # Update document reference when found
                    if "[Document:" in line:
                        current_doc_ref = line.strip()
                        continue
                        
                    # Update context buffer (maintain a 5-line context)
                    context_buffer.append(line)
                    if len(context_buffer) > 5:
                        context_buffer.pop(0)
                    
                    # Check for requirement indicators
                    for indicator in requirement_indicators:
                        if indicator in line.lower():
                            # Get the full context for more complete requirement
                            context = " ".join(context_buffer).strip()
                            
                            # Try to extract just the requirement sentence
                            sentences = re.split(r'(?<=[.!?])\s+', context)
                            for sentence in sentences:
                                if indicator in sentence.lower() and len(sentence) > 15:
                                    # Look for a potential condition ID in this or nearby lines
                                    condition_id = None
                                    for j in range(max(0, i-2), min(len(lines), i+3)):
                                        id_match = re.search(r'C-\d+', lines[j])
                                        if id_match:
                                            condition_id = id_match.group(0)
                                            break
                                    
                                    if not condition_id:
                                        condition_id = f"C-{len(parsed)+1}"
                                    
                                    # Skip if not a meaningful condition
                                    if not ParserUtils.is_meaningful_condition(sentence):
                                        continue
                                        
                                    # Determine category
                                    category = ParserUtils.determine_condition_category(sentence)
                                    
                                    parsed.append({
                                        "id": condition_id,
                                        "description": sentence.strip(),
                                        "reference": current_doc_ref,
                                        "category": category
                                    })
                                    break
                            break
            #############################
            # Check for duplicate condition IDs and fix
            seen_ids = set()
            for condition in parsed:
                condition_id = condition['id']
                if condition_id in seen_ids:
                    # Find the next available ID
                    base_id = condition_id.split('-')[0]
                    suffix = int(condition_id.split('-')[1])
                    while f"{base_id}-{suffix}" in seen_ids:
                        suffix += 1
                    condition['id'] = f"{base_id}-{suffix}"
                seen_ids.add(condition['id'])
            
            # Sort the conditions by ID using natural sort
            parsed.sort(key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
            
        except Exception as e:
            logger.error(f"Error parsing conditions: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "C-1",
                "description": "Failed to parse conditions. Please check the input format.",
                "reference": "Error",
                "category": "General Requirements"
            }]
        
        return parsed
    
    @staticmethod
    def determine_risk_category(risk_type: str, description: str) -> str:
        """Categorize risks based on type and description content"""
        description_lower = description.lower()
        
        # If risk type is provided, use that as primary categorization
        if risk_type:
            risk_categories = {
                "Financial": ["financial", "cost", "budget", "expense", "funding", "monetary"],
                "Operational": ["operational", "process", "workflow", "efficiency", "operation"],
                "Compliance": ["compliance", "regulatory", "regulation", "law", "requirement"],
                "Legal": ["legal", "litigation", "lawsuit", "court", "judiciary"],
                "Reputational": ["reputation", "brand", "public", "perception", "image"],
                "Security": ["security", "cyber", "hack", "breach", "unauthorized", "access"],
                "Safety": ["safety", "injury", "health", "hazard", "danger"]
            }
            
            # Check if the provided risk type matches our categories
            for category, keywords in risk_categories.items():
                if risk_type.lower() in [k.lower() for k in keywords]:
                    return category
            
            # If provided type is already one of our categories, use it
            if risk_type in risk_categories.keys():
                return risk_type
        
        # If no matching risk type, determine from description
        categories = {
            "Data Protection": ["data", "information", "privacy", "confidential", "sensitive"],
            "Access Control": ["access", "authentication", "authorization", "credential"],
            "Compliance": ["comply", "compliance", "regulatory", "regulation", "requirement"],
            "Operational": ["operation", "process", "procedure", "workflow", "efficiency"],
            "Financial": ["financial", "cost", "expense", "budget", "penalty", "fine"],
            "Security": ["security", "breach", "attack", "vulnerability", "threat"],
            "Reporting": ["report", "document", "notification", "disclosure"],
            "Governance": ["governance", "oversight", "management", "accountability"]
        }
        
        # Find matching categories
        matched_categories = []
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                matched_categories.append(category)
        
        if matched_categories:
            # Return the first matched category
            return matched_categories[0]
        
        # Default category
        return "General Risk"
    
    @staticmethod
    def parse_risks(risks_text: str) -> List[Dict[str, Any]]:
        """
        Parse risk text into a standardized structure.
        Works with multiple input formats.
        """
        parsed = []
        
        try:
            # Pattern for structured risk entries
            risk_patterns = [
                # Format: ### R-123
                re.compile(r'###\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Likelihood\*\*:\s*(.*?)\n\*\*Impact\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL),
                
                # Format: ## R-123: C-456
                re.compile(r'##\s*(R-\d+):\s*(C-\d+)\s*\n', re.DOTALL),
                
                # Format with description and source separate lines
                re.compile(r'##\s*(R-\d+).*?\n\*\*Description\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n|$)', re.DOTALL),
                
                # Format: #### R-123: C-456
                re.compile(r'####\s*(R-\d+):\s*(C-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Likelihood\*\*:\s*(.*?)\n\*\*Impact\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            ]
            
            # Track condition mapping for many-to-many relationships
            condition_mapping = {}
            
            # Try each structured pattern
            matched = False
            for pattern in risk_patterns:
                matches = list(pattern.finditer(risks_text))
                if matches:
                    matched = True
                    for match in matches:
                        # Handle the different patterns
                        if len(match.groups()) >= 5:  # Pattern 1 (### R-123) or Pattern 4 (#### R-123: C-456)
                            risk_id = match.group(1).strip()
                            
                            if len(match.groups()) >= 6:  # Pattern 4
                                condition_id = match.group(2).strip()
                                description = match.group(3).strip()
                                likelihood = match.group(4).strip()
                                impact = match.group(5).strip()
                                reference = match.group(6).strip()
                            else:  # Pattern 1
                                description = match.group(2).strip()
                                likelihood = match.group(3).strip()
                                impact = match.group(4).strip()
                                reference = match.group(5).strip()
                                
                                # Infer condition ID from risk ID or from description
                                condition_ids = []
                                cond_matches = re.findall(r'C-\d+', description)
                                if cond_matches:
                                    condition_ids = cond_matches
                                else:
                                    condition_ids = [f"C-{risk_id.replace('R-', '')}"]
                                
                                # Use the first one as primary but track all
                                condition_id = condition_ids[0] if condition_ids else f"C-{risk_id.replace('R-', '')}"
                                
                                # Store mapping for many-to-many relationship
                                condition_mapping[risk_id] = condition_ids
                        elif len(match.groups()) >= 3 and "Description" in match.group(0) and "Source" in match.group(0):  # Pattern 3
                            risk_id = match.group(1).strip()
                            description = match.group(2).strip()
                            reference = match.group(3).strip()
                            
                            # Set default values for likelihood and impact
                            likelihood = "Medium"
                            impact = "Medium"
                            
                            # Extract condition IDs from description
                            condition_ids = re.findall(r'C-\d+', description)
                            condition_id = condition_ids[0] if condition_ids else f"C-{risk_id.replace('R-', '')}"
                            
                            # Store mapping for many-to-many relationship
                            condition_mapping[risk_id] = condition_ids if condition_ids else [condition_id]
                        else:  # Pattern 2 (## R-123: C-456)
                            risk_id = match.group(1).strip()
                            condition_id = match.group(2).strip()
                            
                            # Look for description elsewhere
                            desc_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Description\*\*:\s*(.*?)\n', risks_text, re.DOTALL)
                            source_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Source\*\*:\s*(.*?)(?:\n|$)', risks_text, re.DOTALL)
                            likelihood_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Likelihood\*\*:\s*(.*?)\n', risks_text, re.DOTALL)
                            impact_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Impact\*\*:\s*(.*?)\n', risks_text, re.DOTALL)
                            
                            description = desc_match.group(1).strip() if desc_match else f"Risk associated with {condition_id}"
                            reference = source_match.group(1).strip() if source_match else "Unknown"
                            likelihood = likelihood_match.group(1).strip() if likelihood_match else "Medium"
                            impact = impact_match.group(1).strip() if impact_match else "Medium"
                            
                            # Check for additional condition IDs in description
                            additional_conditions = re.findall(r'C-\d+', description)
                            all_conditions = [condition_id]
                            if additional_conditions:
                                all_conditions.extend([c for c in additional_conditions if c != condition_id])
                            
                            # Store mapping for many-to-many relationship
                            condition_mapping[risk_id] = all_conditions
                            ######################################
                        # Determine priority based on likelihood and impact
                        priority = "Medium"  # Default
                        if likelihood == "High" and impact == "High":
                            priority = "High"
                        elif likelihood == "Low" and impact == "Low":
                            priority = "Low"
                        
                        # Extract risk type for categorization
                        risk_type = ""
                        type_match = re.search(r'Type:\s*([A-Za-z]+)', description)
                        if type_match:
                            risk_type = type_match.group(1)
                        
                        # Determine risk category
                        category = ParserUtils.determine_risk_category(risk_type, description)
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "condition_ids": condition_mapping.get(risk_id, [condition_id]),
                            "description": description,
                            "likelihood": likelihood,
                            "impact": impact,
                            "priority": priority,
                            "category": category,
                            "reference": reference
                        })
            
            # If no matches found with the standard patterns, try other formats
            if not matched or not parsed:
                # Try the "Risk Analysis Results" format
                section_pattern = re.compile(r'## (High|Medium|Low) Priority Risks\s*\n\n(.*?)(?=##|\Z)', re.DOTALL)
                risk_item_pattern = re.compile(r'### (R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Likelihood\*\*:\s*(.*?)\n\*\*Impact\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
                
                for section_match in section_pattern.finditer(risks_text):
                    priority = section_match.group(1)
                    section_content = section_match.group(2)
                    
                    for risk_match in risk_item_pattern.finditer(section_content):
                        risk_id = risk_match.group(1)
                        description = risk_match.group(2).strip()
                        likelihood = risk_match.group(3).strip()
                        impact = risk_match.group(4).strip()
                        reference = risk_match.group(5).strip()
                        
                        # Extract condition IDs from description
                        condition_ids = re.findall(r'C-\d+', description)
                        if not condition_ids:
                            condition_ids = [f"C-{risk_id.replace('R-', '')}"]
                        
                        condition_id = condition_ids[0]  # Primary condition
                        
                        # Extract risk type for categorization
                        risk_type = ""
                        type_match = re.search(r'Type:\s*([A-Za-z]+)', description)
                        if type_match:
                            risk_type = type_match.group(1)
                        
                        # Determine risk category
                        category = ParserUtils.determine_risk_category(risk_type, description)
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "condition_ids": condition_ids,
                            "description": description,
                            "likelihood": likelihood,
                            "impact": impact,
                            "priority": priority,
                            "category": category,
                            "reference": reference
                        })
            
            # If still no matches found, try the "Condition ID: 123" format
            if not parsed:
                # Try the "Condition ID: 123" format
                condition_pattern = re.compile(r'Condition ID:\s*(\d+)\s*-\s*(.*?)(?:\n|$)', re.DOTALL)
                matches = list(condition_pattern.finditer(risks_text))
                
                if matches:
                    for match in matches:
                        condition_id = f"C-{match.group(1)}"
                        description = match.group(2).strip()
                        
                        risk_id = f"R-{match.group(1)}"
                        
                        # Determine risk category
                        category = ParserUtils.determine_risk_category("", f"Risk of non-compliance with condition {condition_id}: {description}")
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "condition_ids": [condition_id],
                            "description": f"Risk of non-compliance with condition {condition_id}: {description}",
                            "likelihood": "Medium",  # Default values
                            "impact": "Medium",
                            "priority": "Medium",
                            "category": category,
                            "reference": "Risk Assessment Document"  # Default reference
                        })
                else:
                    # Last resort - create single entry from whole text
                    parsed.append({
                        "id": "R-Unknown",
                        "condition_id": "C-Unknown",
                        "condition_ids": ["C-Unknown"],
                        "description": risks_text.strip(),
                        "likelihood": "Medium",
                        "impact": "Medium",
                        "priority": "Medium",
                        "category": "General Risk",
                        "reference": "Unknown"
                    })
            
            # Sort the risks by ID using natural sort
            parsed.sort(key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
            
        except Exception as e:
            logger.error(f"Error parsing risks: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "R-1",
                "condition_id": "C-1",
                "condition_ids": ["C-1"],
                "description": "Failed to parse risks. Please check the input format.",
                "likelihood": "Medium",
                "impact": "Medium",
                "priority": "Medium",
                "category": "General Risk",
                "reference": "Error"
            }]
                
        return parsed
    
    @staticmethod
    def determine_control_category(control_type: str, description: str) -> str:
        """Determine the category of a control based on its type and description"""
        description_lower = description.lower()
        
        # Control categories based on common frameworks
        control_categories = {
            "Access Control": ["access", "authentication", "authorization", "credential", "login", "password"],
            "Change Management": ["change", "modification", "update", "version", "release"],
            "Configuration Management": ["configuration", "settings", "parameter", "setup"],
            "Data Protection": ["data", "information", "encryption", "protection", "confidential"],
            "Incident Management": ["incident", "breach", "event", "response", "recovery"],
            "Security Monitoring": ["monitor", "detect", "alert", "surveillance", "logging"],
            "Physical Security": ["physical", "facility", "premise", "building", "location"],
            "Risk Management": ["risk", "assessment", "mitigation", "treatment"],
            "Compliance": ["comply", "compliance", "regulation", "regulatory", "requirement"],
            "Business Continuity": ["continuity", "disaster", "recovery", "backup", "resilience"],
            "Security Awareness": ["awareness", "training", "education", "knowledge"]
        }
        
        # First try to match based on description
        for category, keywords in control_categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        # If no match, use control type for categorization
        if control_type:
            if control_type == "Preventive":
                return "Preventive Controls"
            elif control_type == "Detective":
                return "Detective Controls"
            elif control_type == "Corrective":
                return "Corrective Controls"
            elif control_type == "Administrative":
                return "Administrative Controls"
            elif control_type == "Technical":
                return "Technical Controls"
            elif control_type == "Physical":
                return "Physical Controls"
        
        # Default category
        return "General Controls"
        
    @staticmethod
    def format_conditions(conditions: List[Dict[str, Any]]) -> str:
        """Format conditions with categorization"""
        # Group conditions by category
        categories = {}
        for condition in conditions:
            category = condition.get('category', 'General Requirements')
            if category not in categories:
                categories[category] = []
            categories[category].append(condition)
        
        output = "# 1. Policy Compliance Conditions\n\n"
        
        for category, cat_conditions in sorted(categories.items()):
            output += f"## {category}\n\n"
            
            # Sort conditions by ID within each category
            sorted_conditions = sorted(cat_conditions, key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
            
            for condition in sorted_conditions:
                output += f"### {condition.get('id', 'Unknown')}\n"
                output += f"**Description:** {condition.get('description', 'No description')}\n"
                output += f"**Reference:** {condition.get('reference', 'Unknown')}\n\n"
            
        return output
        
    @staticmethod
    def format_risks(risks: List[Dict[str, Any]]) -> str:
        """Format risks with categorization"""
        # First group risks by priority
        priorities = {
            "High": [],
            "Medium": [],
            "Low": []
        }
        
        for risk in risks:
            priority = risk.get('priority', 'Medium')
            priorities[priority].append(risk)
        
        output = "# 2. Risk Analysis Results\n\n"
        
        # Process each priority level
        for priority in ["High", "Medium", "Low"]:
            priority_risks = priorities[priority]
            
            if priority_risks:
                output += f"## {priority} Priority Risks\n\n"
                
                # Group risks by category within priority
                categories = {}
                for risk in priority_risks:
                    category = risk.get('category', 'General Risk')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(risk)
                
                # Process each category
                for category, cat_risks in sorted(categories.items()):
                    output += f"### {category}\n\n"
                    
                    # Sort risks by ID within each category
                    sorted_risks = sorted(cat_risks, key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
                    
                    for risk in sorted_risks:
                        output += f"#### {risk.get('id', 'Unknown')}\n"
                        output += f"**Description**: {risk.get('description', 'No description')}\n"
                        output += f"**Likelihood**: {risk.get('likelihood', 'Medium')}\n"
                        output += f"**Impact**: {risk.get('impact', 'Medium')}\n"
                        output += f"**Source**: {risk.get('reference', 'Unknown')}\n\n"
        
        return output
    
    @staticmethod
    def format_controls(controls: List[Dict[str, Any]]) -> str:
        """Format controls with categorization"""
        # Group controls by category
        categories = {}
        
        for control in controls:
            category = control.get('category', control.get('type', 'General Controls'))
            if category not in categories:
                categories[category] = []
            categories[category].append(control)
        
        output = "# 3. Control Framework\n\n"
        
        for category, cat_controls in sorted(categories.items()):
            output += f"## {category}\n\n"
            
            # Sort controls by ID within each category
            sorted_controls = sorted(cat_controls, key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
            
            for control in sorted_controls:
                # List all risks this control addresses
                risk_ids = control.get('risk_ids', [control.get('risk_id', 'Unknown')])
                risk_text = ', '.join(risk_ids) if len(risk_ids) > 1 else risk_ids[0]
                
                output += f"### {control.get('id', 'Unknown')}: {risk_text}\n"
                output += f"**Description**: {control.get('description', 'No description')}\n"
                output += f"**Type**: {control.get('type', 'Unknown')}\n"
                output += f"**Source**: {control.get('reference', 'Unknown')}\n"
                output += f"**Implementation Considerations**: {control.get('implementation', 'Regular monitoring and verification required.')}\n\n"
        
        return output
    
    @staticmethod
    def format_test_procedures(procedures: List[Dict[str, Any]]) -> str:
        """Format test procedures with categorization"""
        # Group tests by category
        categories = {}
        
        for proc in procedures:
            # Derive category from control category or test objective
            category = proc.get('category', 'General Test Procedures')
            if category not in categories:
                categories[category] = []
            categories[category].append(proc)
        
        output = "# 4. Audit Test Procedures\n\n"
        
        for category, cat_procs in sorted(categories.items()):
            output += f"## {category}\n\n"
            
            # Sort tests by ID within each category
            sorted_procs = sorted(cat_procs, key=lambda x: ParserUtils.natural_sort_key(x.get('test_id', '')))
            
            for proc in sorted_procs:
                # List all controls this test addresses
                control_ids = proc.get('control_ids', [proc.get('control_id', 'Unknown')])
                control_text = ', '.join(control_ids) if len(control_ids) > 1 else control_ids[0]
                
                output += f"### {proc.get('test_id', 'Unknown')}: {control_text}\n"
                output += f"**Objective**: {proc.get('objective', 'Verify control effectiveness')}\n"
                output += "**Test Steps**:\n"
                for step in proc.get('steps', ['No steps defined']):
                    output += f"- {step}\n"
                output += f"**Required Evidence**: {proc.get('evidence', 'Documentation')}\n"
                output += f"**Source**: {proc.get('reference', 'Unknown')}\n\n"
        
        return output
    
    @staticmethod
    def create_relationship_matrix(conditions: List[Dict[str, Any]], 
                                   risks: List[Dict[str, Any]],
                                   controls: List[Dict[str, Any]],
                                   tests: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
        """
        Create a comprehensive relationship matrix showing the mapping between 
        categories of conditions, risks, controls, and tests.
        """
        # Create category mappings
        condition_categories = {}
        risk_categories = {}
        control_categories = {}
        test_categories = {}
        
        # Map conditions to categories
        for condition in conditions:
            category = condition.get('category', 'General Requirements')
            condition_id = condition.get('id', '')
            if category not in condition_categories:
                condition_categories[category] = []
            condition_categories[category].append(condition_id)
        
        # Map risks to categories
        for risk in risks:
            category = risk.get('category', 'General Risk')
            risk_id = risk.get('id', '')
            if category not in risk_categories:
                risk_categories[category] = []
            risk_categories[category].append(risk_id)
        
        # Map controls to categories
        for control in controls:
            category = control.get('category', control.get('type', 'General Controls'))
            control_id = control.get('id', '')
            if category not in control_categories:
                control_categories[category] = []
            control_categories[category].append(control_id)
        
        # Map tests to categories
        for test in tests:
            category = test.get('category', 'General Test Procedures')
            test_id = test.get('test_id', '')
            if category not in test_categories:
                test_categories[category] = []
            test_categories[category].append(test_id)
        
        # Create relationships between categories
        relationships = {
            'condition_to_risk': {},
            'risk_to_control': {},
            'control_to_test': {}
        }
        
        # Map condition categories to risk categories
        for condition_category, condition_ids in condition_categories.items():
            relationships['condition_to_risk'][condition_category] = {}
            
            for risk in risks:
                risk_category = risk.get('category', 'General Risk')
                if risk_category not in relationships['condition_to_risk'][condition_category]:
                    relationships['condition_to_risk'][condition_category][risk_category] = []
                
                # Check if this risk relates to any conditions in this category
                risk_condition_ids = risk.get('condition_ids', [risk.get('condition_id', '')])
                if any(cond_id in condition_ids for cond_id in risk_condition_ids):
                    relationships['condition_to_risk'][condition_category][risk_category].append(risk.get('id', ''))
        
        # Map risk categories to control categories
        for risk_category, risk_ids in risk_categories.items():
            relationships['risk_to_control'][risk_category] = {}
            
            for control in controls:
                control_category = control.get('category', control.get('type', 'General Controls'))
                if control_category not in relationships['risk_to_control'][risk_category]:
                    relationships['risk_to_control'][risk_category][control_category] = []
                
                # Check if this control relates to any risks in this category
                control_risk_ids = control.get('risk_ids', [control.get('risk_id', '')])
                if any(r_id in risk_ids for r_id in control_risk_ids):
                    relationships['risk_to_control'][risk_category][control_category].append(control.get('id', ''))
        
        # Map control categories to test categories
        for control_category, control_ids in control_categories.items():
            relationships['control_to_test'][control_category] = {}
            
            for test in tests:
                test_category = test.get('category', 'General Test Procedures')
                if test_category not in relationships['control_to_test'][control_category]:
                    relationships['control_to_test'][control_category][test_category] = []
                
                # Check if this test relates to any controls in this category
                test_control_ids = test.get('control_ids', [test.get('control_id', '')])
                if any(c_id in control_ids for c_id in test_control_ids):
                    relationships['control_to_test'][control_category][test_category].append(test.get('test_id', ''))
        
        return relationships
    
    @staticmethod
    def generate_category_mapping_table(relationships: Dict[str, Dict[str, Dict[str, List[str]]]]) -> str:
        """Generate a traceability table showing relationships between categories"""
        output = "# 5. Traceability Matrix by Category\n\n"
        
        # Condition to Risk mappings
        output += "## Condition Categories to Risk Categories\n\n"
        output += "| Condition Category | Risk Category | Sample IDs |\n"
        output += "|---------------------|---------------|------------|\n"
        
        for condition_category, risk_mapping in sorted(relationships['condition_to_risk'].items()):
            for risk_category, risk_ids in sorted(risk_mapping.items()):
                if risk_ids:  # Only show non-empty relationships
                    # Limit to first 5 IDs for readability
                    sample_ids = ', '.join(sorted(risk_ids, key=ParserUtils.natural_sort_key)[:5])
                    if len(risk_ids) > 5:
                        sample_ids += ", ..."
                    
                    output += f"| {condition_category} | {risk_category} | {sample_ids} |\n"
        
        # Risk to Control mappings
        output += "\n## Risk Categories to Control Categories\n\n"
        output += "| Risk Category | Control Category | Sample IDs |\n"
        output += "|---------------|------------------|------------|\n"
        
        for risk_category, control_mapping in sorted(relationships['risk_to_control'].items()):
            for control_category, control_ids in sorted(control_mapping.items()):
                if control_ids:  # Only show non-empty relationships
                    # Limit to first 5 IDs for readability
                    sample_ids = ', '.join(sorted(control_ids, key=ParserUtils.natural_sort_key)[:5])
                    if len(control_ids) > 5:
                        sample_ids += ", ..."
                    
                    output += f"| {risk_category} | {control_category} | {sample_ids} |\n"
        
        # Control to Test mappings
        output += "\n## Control Categories to Test Categories\n\n"
        output += "| Control Category | Test Category | Sample IDs |\n"
        output += "|------------------|---------------|------------|\n"
        
        for control_category, test_mapping in sorted(relationships['control_to_test'].items()):
            for test_category, test_ids in sorted(test_mapping.items()):
                if test_ids:  # Only show non-empty relationships
                    # Limit to first 5 IDs for readability
                    sample_ids = ', '.join(sorted(test_ids, key=ParserUtils.natural_sort_key)[:5])
                    if len(test_ids) > 5:
                        sample_ids += ", ..."
                    
                    output += f"| {control_category} | {test_category} | {sample_ids} |\n"
        
        return output
    
    @staticmethod
    def generate_detailed_mapping_table(conditions: List[Dict[str, Any]], 
                                       risks: List[Dict[str, Any]],
                                       controls: List[Dict[str, Any]],
                                       tests: List[Dict[str, Any]]) -> str:
        """Generate a detailed traceability table from all items"""
        # Build mappings for faster lookups
        condition_map = {c.get('id', ''): c for c in conditions}
        risk_map = {r.get('id', ''): r for r in risks}
        control_map = {c.get('id', ''): c for c in controls}
        test_map = {t.get('test_id', ''): t for t in tests}
        
        # Track traceability relationships
        traceable_items = []
        
        # Start with conditions
        for condition in conditions:
            condition_id = condition.get('id', '')
            condition_category = condition.get('category', 'General Requirements')
            
            # Find risks related to this condition
            related_risks = []
            for risk in risks:
                risk_condition_ids = risk.get('condition_ids', [risk.get('condition_id', '')])
                if condition_id in risk_condition_ids:
                    related_risks.append(risk.get('id', ''))
            
            # For each related risk, find controls
            related_controls = set()
            for risk_id in related_risks:
                for control in controls:
                    control_risk_ids = control.get('risk_ids', [control.get('risk_id', '')])
                    if risk_id in control_risk_ids:
                        related_controls.add(control.get('id', ''))
            
            # For each related control, find tests
            related_tests = set()
            for control_id in related_controls:
                for test in tests:
                    test_control_ids = test.get('control_ids', [test.get('control_id', '')])
                    if control_id in test_control_ids:
                        related_tests.add(test.get('test_id', ''))
            
            # Add to traceable items
            for risk_id in related_risks:
                risk = risk_map.get(risk_id, {})
                risk_category = risk.get('category', 'General Risk')
                risk_priority = risk.get('priority', 'Medium')
                
                for control_id in related_controls:
                    control = control_map.get(control_id, {})
                    control_category = control.get('category', control.get('type', 'General Controls'))
                    
                    for test_id in related_tests:
                        test = test_map.get(test_id, {})
                        test_category = test.get('category', 'General Test Procedures')
                        
                        traceable_items.append({
                            'condition_id': condition_id,
                            'condition_category': condition_category,
                            'risk_id': risk_id,
                            'risk_category': risk_category,
                            'risk_priority': risk_priority,
                            'control_id': control_id,
                            'control_category': control_category,
                            'test_id': test_id,
                            'test_category': test_category
                        })
        
        # Sort traceable items
        traceable_items.sort(key=lambda x: (
            {'High': 0, 'Medium': 1, 'Low': 2}.get(x['risk_priority'], 1),
            ParserUtils.natural_sort_key(x['condition_id']),
            ParserUtils.natural_sort_key(x['risk_id']),
            ParserUtils.natural_sort_key(x['control_id']),
            ParserUtils.natural_sort_key(x['test_id'])
        ))
        
        # Generate table
        output = "# 6. Detailed Traceability Matrix\n\n"
        output += "| Condition ID | Risk ID | Control ID | Test ID | Risk Priority |\n"
        output += "|--------------|---------|------------|---------|---------------|\n"
        
        # Deduplicate rows
        seen = set()
        for item in traceable_items:
            row_key = f"{item['condition_id']}|{item['risk_id']}|{item['control_id']}|{item['test_id']}"
            if row_key not in seen:
                output += f"| {item['condition_id']} | {item['risk_id']} | {item['control_id']} | {item['test_id']} | {item['risk_priority']} |\n"
                seen.add(row_key)
        
        return output