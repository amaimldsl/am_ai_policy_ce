# tools/RiskAnalysisTool.py - Enhanced version
from typing import Optional, List, Dict, Any
from crewai.tools import BaseTool
import logging
import re

from tools.Parser_Utils import ParserUtils

logger = logging.getLogger(__name__)

class RiskAnalysisTool(BaseTool):
    name: str = "Risk Analysis Tool"
    description: str = "Analyzes compliance conditions to identify and categorize risks."
    
    def _run(self, 
             conditions: str,
             action: str = "analyze",  # analyze, categorize, prioritize
             criteria: Optional[str] = None,
             **kwargs) -> str:
        try:
            if action == "analyze":
                # Parse the conditions list using centralized parser
                parsed_conditions = ParserUtils.parse_conditions(conditions)
                
                # Generate risk analysis
                risk_analysis = self._analyze_risks(parsed_conditions)
                
                # Format using standard formatter - enhanced to include categories
                return self._format_risks_with_categories(risk_analysis)
                
            elif action == "categorize":
                return self._categorize_risks(conditions, criteria)
                
            elif action == "prioritize":
                return self._prioritize_risks(conditions, criteria)
                
            return f"Invalid action: {action}. Supported actions: analyze, categorize, prioritize."
            
        except Exception as e:
            logger.error(f"Error in RiskAnalysisTool: {str(e)}", exc_info=True)
            return f"Error analyzing risks: {str(e)}"
    
    def _analyze_risks(self, conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate risk analysis from conditions with improved categorization"""
        risk_analysis = []
        
        for condition in conditions:
            # Generate risk ID based on condition ID
            condition_id = condition['id']
            risk_id = f"R-{condition_id.replace('C-', '')}"
            
            # Get condition description
            condition_desc = condition.get('description', '')
            
            # Analyze the type of risk based on condition text
            risk_type, likelihood, impact, risk_category = self._determine_risk_factors(condition_desc)
            
            # Generate comprehensive risk description
            risk_desc = f"Risk of non-compliance with {condition_id}: {condition_desc}"
            
            # Determine priority based on likelihood and impact
            priority = self._determine_priority(likelihood, impact)
            
            # Add to analysis results
            risk_analysis.append({
                "id": risk_id,
                "condition_id": condition_id,
                "condition_ids": [condition_id],  # For many-to-many relationships
                "description": risk_desc,
                "type": risk_type,
                "category": risk_category,
                "likelihood": likelihood,
                "impact": impact,
                "priority": priority,
                "reference": condition.get("reference", "")
            })
        
        return risk_analysis
    
    def _determine_risk_factors(self, condition_text: str) -> tuple:
        """Analyze condition text to determine risk type, likelihood, impact, and category"""
        # Default values
        risk_type = "Compliance"
        likelihood = "Medium"
        impact = "Medium"
        
        # ENHANCED: More comprehensive risk categorization
        risk_categories = {
            "Access Control": ['access', 'authenticat', 'authoriz', 'login', 'password', 'credential', 'identity'],
            "Data Protection": ['data', 'information', 'confidential', 'encrypt', 'backup', 'sensitive', 'privacy'],
            "Security": ['security', 'protect', 'threat', 'vulnerability', 'attack', 'malware', 'virus'],
            "Regulatory": ['regulation', 'compliance', 'legal', 'law', 'statute', 'requirement', 'standard'],
            "Operational": ['operation', 'process', 'procedure', 'workflow', 'function', 'business', 'activity'],
            "Reporting": ['report', 'document', 'record', 'log', 'audit', 'monitor', 'evidence'],
            "Training": ['train', 'education', 'awareness', 'knowledge', 'skill', 'competency', 'learning'],
            "Third Party": ['vendor', 'supplier', 'third party', 'outsource', 'contract', 'provider', 'partner'],
            "Business Continuity": ['continuity', 'disaster', 'recovery', 'backup', 'resilience', 'incident', 'emergency']
        }
        
        # Determine risk category
        risk_category = "General"
        max_matches = 0
        
        for category, keywords in risk_categories.items():
            matches = sum(1 for keyword in keywords if keyword in condition_text.lower())
            if matches > max_matches:
                max_matches = matches
                risk_category = category
        
        # Keywords that might indicate higher likelihood
        high_likelihood_indicators = ['always', 'must', 'shall', 'all', 'every', 'critical', 
                                      'frequent', 'common', 'certain', 'regular', 'often']
        
        # Keywords that might indicate lower likelihood
        low_likelihood_indicators = ['rare', 'unlikely', 'seldom', 'infrequent', 'occasional', 
                                     'uncommon', 'sometimes', 'may', 'might', 'could']
        
        # Keywords that might indicate higher impact
        high_impact_indicators = ['severe', 'significant', 'major', 'critical', 'essential', 
                                  'safety', 'security', 'legal', 'regulatory', 'penalty', 'fine',
                                  'substantial', 'extensive', 'serious', 'breach', 'violation']
        
        # Keywords that might indicate lower impact
        low_impact_indicators = ['minor', 'minimal', 'trivial', 'small', 'limited', 
                                'slight', 'modest', 'moderate', 'marginal', 'insignificant']
        
        # Check for likelihood indicators
        if any(indicator in condition_text.lower() for indicator in high_likelihood_indicators):
            likelihood = "High"
        elif any(indicator in condition_text.lower() for indicator in low_likelihood_indicators):
            likelihood = "Low"
            
        # Check for impact indicators
        if any(indicator in condition_text.lower() for indicator in high_impact_indicators):
            impact = "High"
        elif any(indicator in condition_text.lower() for indicator in low_impact_indicators):
            impact = "Low"
            
        # Determine risk type
        if 'financial' in condition_text.lower() or 'cost' in condition_text.lower() or 'budget' in condition_text.lower():
            risk_type = "Financial"
        elif 'reputation' in condition_text.lower() or 'brand' in condition_text.lower() or 'public' in condition_text.lower():
            risk_type = "Reputational"
        elif 'legal' in condition_text.lower() or 'law' in condition_text.lower() or 'regulation' in condition_text.lower():
            risk_type = "Legal"
        elif 'security' in condition_text.lower() or 'threat' in condition_text.lower() or 'vulnerability' in condition_text.lower():
            risk_type = "Security"
        elif 'safety' in condition_text.lower() or 'health' in condition_text.lower() or 'injury' in condition_text.lower():
            risk_type = "Safety"
        elif 'operation' in condition_text.lower() or 'process' in condition_text.lower() or 'function' in condition_text.lower():
            risk_type = "Operational"
            
        return risk_type, likelihood, impact, risk_category
    
    def _determine_priority(self, likelihood: str, impact: str) -> str:
        """Determine risk priority based on likelihood and impact"""
        # Risk priority matrix
        priority_matrix = {
            # High impact
            ('High', 'High'): 'High',
            ('Medium', 'High'): 'High',
            ('Low', 'High'): 'Medium',
            
            # Medium impact
            ('High', 'Medium'): 'High',
            ('Medium', 'Medium'): 'Medium',
            ('Low', 'Medium'): 'Low',
            
            # Low impact
            ('High', 'Low'): 'Medium',
            ('Medium', 'Low'): 'Low',
            ('Low', 'Low'): 'Low',
        }
        
        return priority_matrix.get((likelihood, impact), 'Medium')
    
    def _format_risks_with_categories(self, risks: List[Dict[str, Any]]) -> str:
        """Format risks output with categories and without separator lines"""
        # Group risks by category
        categorized_risks = {}
        
        for risk in risks:
            category = risk.get('category', 'General')
            if category not in categorized_risks:
                categorized_risks[category] = []
            categorized_risks[category].append(risk)
        
        # Output with categories
        output = "# 02_Risk Analysis Results\n\n"
        
        # Also group by priority within each category
        for category, category_risks in categorized_risks.items():
            output += f"## {category} Risks\n\n"
            
            # Group by priority
            priority_groups = {
                "High": [],
                "Medium": [],
                "Low": []
            }
            
            for risk in category_risks:
                priority = risk.get('priority', 'Medium')
                priority_groups[priority].append(risk)
            
            # Output by priority (highest first)
            for priority in ["High", "Medium", "Low"]:
                priority_risks = priority_groups[priority]
                if priority_risks:
                    output += f"### {priority} Priority\n\n"
                    
                    # Sort risks by ID
                    sorted_risks = sorted(priority_risks, key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
                    
                    for risk in sorted_risks:
                        output += f"#### {risk.get('id', 'Unknown')}\n\n"
                        output += f"**Description**: {risk.get('description', 'No description')}\n\n"
                        output += f"**Likelihood**: {risk.get('likelihood', 'Medium')}\n\n"
                        output += f"**Impact**: {risk.get('impact', 'Medium')}\n\n"
                        output += f"**Type**: {risk.get('type', 'Compliance')}\n\n"
                        output += f"**Source**: {risk.get('reference', 'Unknown')}\n\n"
        
        return output
    
    def _categorize_risks(self, risks_text: str, criteria: Optional[str]) -> str:
        """Categorize risks based on specified criteria"""
        try:
            parsed_risks = ParserUtils.parse_risks(risks_text)
            
            if not criteria:
                criteria = "type"  # Default categorization
                
            categories = {}
            
            # Group risks by the specified criteria
            for risk in parsed_risks:
                category_value = risk.get(criteria, "Unknown")
                
                if category_value not in categories:
                    categories[category_value] = []
                    
                categories[category_value].append(risk)
            
            # Format the output
            output = f"# 02_Risk Categorization by {criteria.capitalize()}\n\n"
            
            for category, risks in categories.items():
                output += f"## {category}\n\n"
                
                for risk in risks:
                    output += f"### {risk.get('id', 'Unknown')}\n\n"
                    output += f"**Description**: {risk.get('description', 'No description')}\n\n"
                    output += f"**Related Condition**: {risk.get('condition_id', 'Unknown')}\n\n"
                    output += f"**Likelihood**: {risk.get('likelihood', 'Medium')}\n\n"
                    output += f"**Impact**: {risk.get('impact', 'Medium')}\n\n"
                
            return output
            
        except Exception as e:
            logger.error(f"Error categorizing risks: {str(e)}", exc_info=True)
            return f"Error categorizing risks: {str(e)}"
    
    def _prioritize_risks(self, risks_text: str, criteria: Optional[str]) -> str:
        """Prioritize risks based on specified criteria"""
        try:
            parsed_risks = ParserUtils.parse_risks(risks_text)
            
            # Default prioritization uses both likelihood and impact
            priority_mapping = {
                "High": 3,
                "Medium": 2,
                "Low": 1
            }
            
            # Calculate priority score for each risk
            for risk in parsed_risks:
                likelihood_score = priority_mapping.get(risk.get('likelihood', 'Medium'), 2)
                impact_score = priority_mapping.get(risk.get('impact', 'Medium'), 2)
                
                # Priority score formula
                risk['priority_score'] = likelihood_score * impact_score
                
                # Priority category
                if risk['priority_score'] >= 6:
                    risk['priority'] = "High"
                elif risk['priority_score'] >= 3:
                    risk['priority'] = "Medium"
                else:
                    risk['priority'] = "Low"
            
            # Group risks by priority
            priority_groups = {
                "High": [],
                "Medium": [],
                "Low": []
            }
            
            for risk in parsed_risks:
                priority = risk.get('priority', 'Medium')
                priority_groups[priority].append(risk)
            
            # Format the output
            output = "# 02_Prioritized Risk Register\n\n"
            
            # Output by priority
            for priority in ["High", "Medium", "Low"]:
                priority_risks = priority_groups[priority]
                if priority_risks:
                    output += f"## {priority} Priority Risks\n\n"
                    
                    # Sort risks by ID
                    sorted_risks = sorted(priority_risks, key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
                    
                    for risk in sorted_risks:
                        output += f"### {risk.get('id', 'Unknown')}\n\n"
                        output += f"**Description**: {risk.get('description', 'No description')}\n\n"
                        output += f"**Likelihood**: {risk.get('likelihood', 'Medium')}\n\n"
                        output += f"**Impact**: {risk.get('impact', 'Medium')}\n\n"
                        output += f"**Priority Score**: {risk.get('priority_score', 0)}\n\n"
                        output += f"**Reference**: {risk.get('reference', 'Unknown')}\n\n"
                
            return output
            
        except Exception as e:
            logger.error(f"Error prioritizing risks: {str(e)}", exc_info=True)
            return f"Error prioritizing risks: {str(e)}"