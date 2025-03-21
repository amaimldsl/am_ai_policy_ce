# tools/ControlDesignTool.py - Enhanced version
from typing import Optional, List, Dict, Any
from crewai.tools import BaseTool
import logging
import re
from tools.Parser_Utils import ParserUtils

logger = logging.getLogger(__name__)

class ControlDesignTool(BaseTool):
    name: str = "Control Design Tool"
    description: str = "Designs controls for mitigating identified risks."
    
    def _verify_control_completeness(self, controls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify and enhance control descriptions to ensure they're complete.
        
        Args:
            controls (List[Dict[str, Any]]): The list of control dictionaries
            
        Returns:
            List[Dict[str, Any]]: The enhanced controls with complete descriptions
        """
        
        
        for control in controls:
            # Check and enhance the main description
            description = control.get('description', '')
            if description and not any(description.endswith(c) for c in ['.', '!', '?']):
                control['description'] = ParserUtils.complete_truncated_sentence(description)
                
            # Check and enhance implementation considerations
            implementation = control.get('implementation', '')
            if implementation and not any(implementation.endswith(c) for c in ['.', '!', '?']):
                # Split by sentences and check each one
                sentences = re.split(r'(?<=[.!?])\s+', implementation)
                
                # Check the last sentence for completeness
                if sentences and not any(sentences[-1].endswith(c) for c in ['.', '!', '?']):
                    sentences[-1] = ParserUtils.complete_truncated_sentence(sentences[-1])
                    
                control['implementation'] = ' '.join(sentences)
        
        return controls
    
    
    
    
    def _run(self,
             risks: str,
             action: str = "design",  # design, categorize, evaluate
             framework: Optional[str] = None,
             **kwargs) -> str:
        try:
            if action == "design":
                # Parse the risks using centralized parser
                parsed_risks = ParserUtils.parse_risks(risks)
                
                # Design controls for each risk
                controls = self._design_controls(parsed_risks, framework)
                
                # Format using standard formatter
                return ParserUtils.format_controls(controls)
                
            elif action == "categorize":
                return self._categorize_controls(risks)
                
            elif action == "evaluate":
                return self._evaluate_controls(risks)
                
            return f"Invalid action: {action}. Supported actions: design, categorize, evaluate."
            
        except Exception as e:
            logger.error(f"Error in ControlDesignTool: {str(e)}", exc_info=True)
            return f"Error designing controls: {str(e)}"
    
    def _determine_control_type(self, risk_description: str, available_types: List[str]) -> str:
        """Determine the most appropriate control type based on risk description"""
        # Default to the first available type
        default_type = available_types[0] if available_types else "Preventive"
        
        # Check for keywords that suggest specific control types
        if "detect" in risk_description.lower() and "Detective" in available_types:
            return "Detective"
        elif "prevent" in risk_description.lower() and "Preventive" in available_types:
            return "Preventive"
        elif "correct" in risk_description.lower() and "Corrective" in available_types:
            return "Corrective"
        elif "technical" in risk_description.lower() and "Technical" in available_types:
            return "Technical"
        elif "physical" in risk_description.lower() and "Physical" in available_types:
            return "Physical"
        elif "compensat" in risk_description.lower() and "Compensating" in available_types:
            return "Compensating"
        
        return default_type
    
    def _identify_keywords(self, description: str) -> List[str]:
        """Identify key domain keywords from the risk description for more specific controls"""
        domains = {
            "access": ["access", "authentication", "authorization", "login", "credential", "password", "identity"],
            "data": ["data", "information", "confidential", "encrypt", "protect", "sensitive", "store", "backup"],
            "security": ["security", "cybersecurity", "protection", "vulnerability", "threat", "malware", "attack"],
            "compliance": ["compliance", "regulatory", "regulation", "law", "requirement", "standard", "guideline"],
            "audit": ["audit", "review", "verify", "inspect", "examination", "assessment", "evaluate"],
            "monitoring": ["monitor", "surveillance", "detect", "alert", "observe", "track", "log"],
            "physical": ["physical", "facility", "premise", "building", "location", "site", "area"],
            "training": ["training", "awareness", "education", "instruct", "teach", "learn", "knowledge"],
            "reporting": ["report", "document", "record", "communication", "notify", "inform"],
            "incident": ["incident", "event", "breach", "violation", "issue", "problem", "response"]
        }
        
        found_domains = []
        for domain, keywords in domains.items():
            if any(keyword in description.lower() for keyword in keywords):
                found_domains.append(domain)
        
        return found_domains
    
    def _design_controls(self, risks: List[Dict[str, Any]], framework: Optional[str]) -> List[Dict[str, Any]]:
        """Design controls for each risk - ENHANCED VERSION"""
        controls = []
        
        # Use different control frameworks based on specified framework
        control_types = {
            "NIST": ["Preventive", "Detective", "Corrective", "Compensating"],
            "ISO27001": ["Administrative", "Technical", "Physical"],
            "COBIT": ["Planning", "Implementation", "Delivery", "Monitoring"],
            "Default": ["Preventive", "Detective", "Corrective"]
        }
        
        # Select framework control types
        selected_framework = framework if framework in control_types else "Default"
        available_types = control_types[selected_framework]
        
        # Track condition_id to risk_id mapping to maintain traceability
        condition_risk_mapping = {}
        for risk in risks:
            risk_id = risk.get('id', '')
            condition_ids = risk.get('condition_ids', [risk.get('condition_id', 'Unknown')])
            
            for condition_id in condition_ids:
                if condition_id not in condition_risk_mapping:
                    condition_risk_mapping[condition_id] = []
                condition_risk_mapping[condition_id].append(risk_id)
        
        for risk in risks:
            # Generate control ID based on risk ID
            risk_id = risk.get('id', '')
            
            # Handle cases where ID might not be in expected format
            if risk_id.startswith('R-'):
                base_id = risk_id.replace('R-', '')
                control_id = f"C-{base_id}"
            else:
                # Try to extract numeric part or use a counter
                num_match = re.search(r'\d+', risk_id)
                if num_match:
                    control_id = f"C-{num_match.group(0)}"
                else:
                    control_id = f"C-{len(controls)+1}"
            
            # Get the risk description and condition IDs
            risk_desc = risk.get('description', '')
            condition_ids = risk.get('condition_ids', [risk.get('condition_id', 'Unknown')])
            
            # Identify domain keywords for more targeted controls
            domains = self._identify_keywords(risk_desc)
            
            # Determine the primary control type based on risk content
            primary_control_type = self._determine_control_type(risk_desc, available_types)
            
            # For each risk, create a primary control and at least one secondary control of a different type
            # This ensures more comprehensive coverage
            control_types_to_use = [primary_control_type]
            
            # Add a secondary control type if available
            secondary_types = [t for t in available_types if t != primary_control_type]
            if secondary_types:
                # Pick a secondary type that complements the primary type
                if primary_control_type == "Preventive" and "Detective" in secondary_types:
                    secondary_type = "Detective"
                elif primary_control_type == "Detective" and "Corrective" in secondary_types:
                    secondary_type = "Corrective"
                else:
                    secondary_type = secondary_types[0]
                
                control_types_to_use.append(secondary_type)
            
            # Create controls for each selected type
            for idx, control_type in enumerate(control_types_to_use):
                # Create a specific control ID for each type
                if idx == 0:
                    specific_control_id = control_id
                else:
                    specific_control_id = f"{control_id}-{idx+1}"
                
                # Design specific control based on the risk, control type, and domains
                control_desc = self._generate_specific_control_description(
                    risk_desc, control_type, domains, condition_ids
                )
                
                # Add implementation considerations based on control type and domains
                implementation = self._generate_specific_implementation_guidance(
                    control_type, domains, risk_desc
                )
                
                # Add to controls list with all related risks
                controls.append({
                    "id": specific_control_id,
                    "risk_id": risk_id,
                    "risk_ids": [risk_id],  # Start with current risk
                    "description": control_desc,
                    "type": control_type,
                    "domains": domains,
                    "implementation": implementation,
                    "reference": risk.get("reference", "")
                })
        
        # Process many-to-many relationships for controls
        self._process_control_relationships(controls, risks)
        
        
        controls = self._verify_control_completeness(controls)
        
        return controls

    def _process_control_relationships(self, controls: List[Dict[str, Any]], risks: List[Dict[str, Any]]) -> None:
        """Process and establish many-to-many relationships between controls and risks"""
        # Build risk ID to control ID mappings
        risk_to_controls = {}
        
        # First pass: build initial mappings
        for control in controls:
            risk_id = control.get('risk_id', '')
            if risk_id:
                if risk_id not in risk_to_controls:
                    risk_to_controls[risk_id] = []
                risk_to_controls[risk_id].append(control.get('id', ''))
        
        # Second pass: establish related risks for each control
        for control in controls:
            # Find all risks with similar domains or shared conditions
            control_domains = control.get('domains', [])
            control_risk_id = control.get('risk_id', '')
            
            # Skip if no primary risk
            if not control_risk_id:
                continue
            
            # Find the primary risk object
            primary_risk = next((r for r in risks if r.get('id', '') == control_risk_id), None)
            if not primary_risk:
                continue
            
            # Get condition IDs from primary risk
            primary_conditions = primary_risk.get('condition_ids', [primary_risk.get('condition_id', '')])
            
            # Find other risks that share conditions or domains
            related_risks = []
            for risk in risks:
                risk_id = risk.get('risk_id', risk.get('id', ''))
                
                # Skip if it's the same as the primary risk
                if risk_id == control_risk_id or not risk_id:
                    continue
                
                # Check condition overlap
                risk_conditions = risk.get('condition_ids', [risk.get('condition_id', '')])
                conditions_overlap = any(c in primary_conditions for c in risk_conditions)
                
                # Check domain similarity
                risk_desc = risk.get('description', '')
                risk_domains = self._identify_keywords(risk_desc)
                domains_overlap = any(d in control_domains for d in risk_domains)
                
                # Add to related risks if there's overlap
                if conditions_overlap or domains_overlap:
                    related_risks.append(risk_id)
            
            # Update the control with all related risks
            if related_risks:
                all_risks = [control_risk_id] + related_risks
                control['risk_ids'] = all_risks

    def _generate_specific_control_description(self, risk_description: str, control_type: str, 
                                             domains: List[str], condition_ids: List[str]) -> str:
        """Generate a specific control description based on risk, control type, and domains"""
        # Extract key elements from risk description
        import re
        
        # Try to identify key requirements from risk description
        requirement_match = re.search(r'compliance with (.+?)(?:$|\.)', risk_description)
        requirement = requirement_match.group(1) if requirement_match else "requirements"
        
        # Extract specific non-compliance concerns
        concern_match = re.search(r'Risk of (non-compliance|failure|breach|violation|not adhering) with.*?:(.+?)(?:$|\.)', risk_description, re.IGNORECASE)
        specific_concern = concern_match.group(2).strip() if concern_match else requirement
        
        # Generate domain-specific parts of the control description
        domain_specifics = ""
        if domains:
            if "access" in domains:
                domain_specifics += " This includes implementing proper access controls, authentication mechanisms, and authorization procedures."
            if "data" in domains:
                domain_specifics += " This includes data classification, protection measures, and handling procedures for sensitive information."
            if "security" in domains:
                domain_specifics += " This includes security safeguards, threat mitigation, and protection against vulnerabilities."
            if "compliance" in domains:
                domain_specifics += " This includes regulatory tracking, policy documentation, and compliance verification procedures."
            if "monitoring" in domains:
                domain_specifics += " This includes continuous monitoring, logging, and alerting mechanisms."
        
        # Add reference to all related conditions
        condition_reference = f" Addresses compliance conditions: {', '.join(condition_ids)}." if condition_ids else ""
        
        # Generate appropriate description based on control type
        if control_type == "Preventive":
            return f"Implement specific preventive measures to ensure compliance with {specific_concern} through targeted verification, validation, and restriction mechanisms.{domain_specifics} This control prevents non-compliance before it occurs by enforcing specific requirements at the entry point.{condition_reference}"
        elif control_type == "Detective":
            return f"Establish targeted monitoring and detection systems to identify potential non-compliance with {specific_concern}.{domain_specifics} This control employs specific audits, automated scanning, and exception reporting to detect violations promptly.{condition_reference}"
        elif control_type == "Corrective":
            return f"Develop specific remediation procedures and corrective action plans to address identified instances of non-compliance with {specific_concern}.{domain_specifics} This control ensures timely resolution of compliance issues through structured response mechanisms.{condition_reference}"
        elif control_type == "Compensating":
            return f"Implement alternative controls to achieve equivalent protection when direct compliance with {specific_concern} is not feasible.{domain_specifics} This compensating control addresses the underlying risk through alternative means that provide comparable assurance.{condition_reference}"
        elif control_type == "Technical":
            return f"Deploy specific technical safeguards, system configurations, and automated tools to enforce and verify compliance with {specific_concern}.{domain_specifics} This control uses technology to embed compliance requirements into operational processes.{condition_reference}"
        elif control_type == "Physical":
            return f"Establish specific physical barriers, access controls, and environmental safeguards to ensure compliance with {specific_concern}.{domain_specifics} This control addresses physical aspects of compliance through tangible protections.{condition_reference}"
        elif control_type == "Administrative":
            return f"Develop specific policies, procedures, and governance structures to manage compliance with {specific_concern}.{domain_specifics} This control establishes administrative frameworks that define responsibilities and processes.{condition_reference}"
        
        # Default generic description
        return f"Implement specific controls to ensure compliance with {specific_concern} through a combination of targeted preventive, detective, and corrective measures tailored to the specific requirements.{domain_specifics}{condition_reference}"

    def _generate_specific_implementation_guidance(self, control_type: str, domains: List[str], 
                                                risk_description: str) -> str:
        """Generate specific implementation guidance based on control type and domains"""
        # Base implementation guidance by control type
        base_guidance = self._get_base_implementation_guidance(control_type)
        
        # Add domain-specific implementation guidance
        domain_guidance = []
        
        if "access" in domains:
            domain_guidance.append("Implement role-based access control (RBAC) with principle of least privilege")
            domain_guidance.append("Enforce strong password policies and multi-factor authentication")
            domain_guidance.append("Conduct regular access reviews and promptly remove unnecessary access")
        
        if "data" in domains:
            domain_guidance.append("Classify data according to sensitivity and implement appropriate protection")
            domain_guidance.append("Implement encryption for data at rest and in transit")
            domain_guidance.append("Establish data retention and secure disposal procedures")
        
        if "security" in domains:
            domain_guidance.append("Conduct regular vulnerability assessments and penetration testing")
            domain_guidance.append("Implement security patching and update processes")
            domain_guidance.append("Deploy defense-in-depth security architecture")
        
        if "compliance" in domains:
            domain_guidance.append("Maintain a compliance requirements register with regular updates")
            domain_guidance.append("Conduct periodic compliance self-assessments")
            domain_guidance.append("Establish a documented compliance exception process")
            
        if "audit" in domains:
            domain_guidance.append("Maintain audit trails for all compliance-related activities")
            domain_guidance.append("Establish independent review procedures for key controls")
            domain_guidance.append("Document auditable evidence of control effectiveness")
            
        if "monitoring" in domains:
            domain_guidance.append("Implement automated monitoring tools with defined thresholds")
            domain_guidance.append("Configure real-time alerting for potential compliance violations")
            domain_guidance.append("Establish a formal review process for monitoring results")
            
        if "physical" in domains:
            domain_guidance.append("Implement physical access controls with logging capabilities")
            domain_guidance.append("Establish environmental monitoring for sensitive areas")
            domain_guidance.append("Conduct regular physical security inspections")
            
        if "training" in domains:
            domain_guidance.append("Develop role-specific compliance training materials")
            domain_guidance.append("Establish mandatory training schedule with completion tracking")
            domain_guidance.append("Conduct knowledge assessments after training completion")
        
        if "reporting" in domains:
            domain_guidance.append("Define report templates with all required compliance elements")
            domain_guidance.append("Establish reporting schedules and distribution lists")
            domain_guidance.append("Implement verification procedures for report accuracy")
            
        if "incident" in domains:
            domain_guidance.append("Develop incident response procedures for compliance violations")
            domain_guidance.append("Establish clear escalation paths and communication protocols")
            domain_guidance.append("Implement root cause analysis and remediation tracking")
        
        # Combine base and domain-specific guidance
        combined_guidance = base_guidance
        if domain_guidance:
            combined_guidance += "\n\nDomain-specific implementation measures:\n- " + "\n- ".join(domain_guidance)
        
        return combined_guidance
    
    def _get_base_implementation_guidance(self, control_type: str) -> str:
        """Get base implementation guidance for the control type"""
        if control_type == "Preventive":
            return ("Implement the following preventive measures: (1) Develop specific input validation requirements and automated checks; "
                    "(2) Establish targeted pre-approval workflows with designated approvers; "
                    "(3) Configure system restrictions to enforce specific compliance boundaries; "
                    "(4) Implement automated verification of compliance requirements before processing; "
                    "(5) Conduct focused training on specific compliance requirements for relevant personnel.")
        elif control_type == "Detective":
            return ("Establish the following detection mechanisms: (1) Implement targeted compliance scanning on a defined schedule; "
                    "(2) Configure specific real-time alerts for potential compliance violations; "
                    "(3) Conduct focused compliance audits with detailed documentation; "
                    "(4) Establish specific exception reporting processes with clear escalation procedures; "
                    "(5) Deploy monitoring tools to track specific compliance metrics and trends.")
        elif control_type == "Corrective":
            return ("Develop the following corrective measures: (1) Create detailed incident response procedures for specific compliance violations; "
                    "(2) Establish targeted remediation plans with clear ownership and timelines; "
                    "(3) Implement root cause analysis protocols for specific compliance failures; "
                    "(4) Develop documentation requirements for specific corrective actions; "
                    "(5) Establish verification procedures to confirm effective remediation.")
        elif control_type == "Technical":
            return ("Deploy the following technical controls: (1) Implement automated enforcement through specific system configurations; "
                    "(2) Establish technical safeguards to prevent specific compliance violations; "
                    "(3) Configure detailed logging and monitoring for compliance-related events; "
                    "(4) Implement access controls aligned with specific compliance requirements; "
                    "(5) Develop automated testing procedures for technical compliance verification.")
        elif control_type == "Physical":
            return ("Implement the following physical controls: (1) Establish specific physical access restrictions to sensitive areas; "
                    "(2) Deploy environmental monitoring for compliance-critical resources; "
                    "(3) Implement physical security measures aligned with specific requirements; "
                    "(4) Establish verification procedures for physical security controls; "
                    "(5) Develop physical inventory management aligned with compliance needs.")
        elif control_type == "Administrative":
            return ("Establish the following administrative measures: (1) Develop comprehensive policies addressing specific compliance requirements; "
                    "(2) Create procedural documents with step-by-step compliance instructions; "
                    "(3) Establish governance structures with clear compliance responsibilities; "
                    "(4) Implement targeted training programs for specific compliance requirements; "
                    "(5) Develop documentation standards for demonstrating compliance.")
        
        # Default guidance for other control types
        return ("Implementation guidance: (1) Identify key stakeholders and establish clear ownership; "
                "(2) Develop detailed procedures aligned with the specific control objectives; "
                "(3) Establish metrics to measure specific control effectiveness; "
                "(4) Implement regular testing to verify control performance; "
                "(5) Establish documentation requirements to demonstrate compliance.")
    
    def _categorize_controls(self, controls_text: str) -> str:
        """Categorize controls by type"""
        try:
            parsed_controls = ParserUtils.parse_controls(controls_text)
            
            # Group controls by type
            categories = {}
            for control in parsed_controls:
                control_type = control.get('type', 'Undefined')
                
                if control_type not in categories:
                    categories[control_type] = []
                    
                categories[control_type].append(control)
            
            # Format the output
            output = "# Controls Categorized by Type\n\n"
            
            for category, controls in categories.items():
                output += f"## {category} Controls\n"
                
                # Sort controls by ID within each category
                sorted_controls = sorted(controls, key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
                
                for control in sorted_controls:
                    # List all risks this control addresses
                    risk_ids = control.get('risk_ids', [control.get('risk_id', 'Unknown')])
                    risk_text = ', '.join(risk_ids) if len(risk_ids) > 1 else risk_ids[0]
                    
                    output += f"- {control.get('id', 'Unknown')}: {risk_text} - {control.get('description', 'No description')[:100]}...\n"
                
                output += "\n"
                
            return output
            
        except Exception as e:
            logger.error(f"Error categorizing controls: {str(e)}", exc_info=True)
            return f"Error categorizing controls: {str(e)}"
    
    def _evaluate_controls(self, controls_text: str) -> str:
        """Evaluate controls for completeness and effectiveness"""
        try:
            parsed_controls = ParserUtils.parse_controls(controls_text)
            
            evaluation_results = []
            
            for control in parsed_controls:
                control_id = control.get('id', 'Unknown')
                description = control.get('description', '')
                control_type = control.get('type', 'Unknown')
                
                # Evaluate description completeness
                description_score = len(description) / 50  # Simple heuristic
                description_score = min(5, description_score)  # Cap at 5
                
                # Evaluate specificity
                specificity_score = 3  # Default medium
                if len(description.split()) > 15:
                    specificity_score = 4
                if len(description.split()) > 30:
                    specificity_score = 5
                
                # Evaluate implementation guidance
                implementation = control.get('implementation', '')
                implementation_score = 2  # Default low
                if implementation and len(implementation) > 20:
                    implementation_score = 4
                if implementation and len(implementation) > 50:
                    implementation_score = 5
                
                # Calculate overall score
                overall_score = (description_score + specificity_score + implementation_score) / 3
                
                # Determine rating
                if overall_score >= 4.5:
                    rating = "Excellent"
                elif overall_score >= 3.5:
                    rating = "Good"
                elif overall_score >= 2.5:
                    rating = "Adequate"
                else:
                    rating = "Needs Improvement"
                
                evaluation_results.append({
                    "control_id": control_id,
                    "description_score": description_score,
                    "specificity_score": specificity_score,
                    "implementation_score": implementation_score,
                    "overall_score": overall_score,
                    "rating": rating
                })
            
            # Format the evaluation results
            output = "# Control Evaluation Results\n\n"
            
            # Sort by control ID
            sorted_results = sorted(evaluation_results, key=lambda x: ParserUtils.natural_sort_key(x['control_id']))
            
            for result in sorted_results:
                output += f"## {result['control_id']}\n"
                output += f"**Description Score**: {result['description_score']:.1f}/5\n"
                output += f"**Specificity Score**: {result['specificity_score']}/5\n"
                output += f"**Implementation Score**: {result['implementation_score']}/5\n"
                output += f"**Overall Score**: {result['overall_score']:.1f}/5\n"
                output += f"**Rating**: {result['rating']}\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error evaluating controls: {str(e)}", exc_info=True)
            return f"Error evaluating controls: {str(e)}"