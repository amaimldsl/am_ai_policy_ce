#!/bin/bash
# Script to execute the Policy Compliance Analysis Framework

# Color codes for formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Policy Compliance Analysis Framework${NC}"

# Ensure we're in the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create necessary directories if they don't exist
mkdir -p config
mkdir -p policy
mkdir -p preprocessed
mkdir -p output
mkdir -p tools

# Check if config files exist, copy from examples if not
if [ ! -f config/agents.yaml ]; then
    echo -e "${YELLOW}Creating default agents.yaml${NC}"
    cat > config/agents.yaml << EOL
policy_analyzer:
  role: Policy Analyzer
  goal: Extract all policy compliance conditions, requirements, and obligations from the PDF
  backstory: You are an expert in policy analysis with experience in regulatory frameworks and compliance requirements extraction.
  tools:
    - PDFTool
    - FileIOTool
  verbose: true

risk_assessor:
  role: Risk Assessor
  goal: Identify and categorize all potential risks associated with each compliance condition
  backstory: You are a risk management professional who specializes in identifying compliance-related risks and their potential impacts.
  tools:
    - FileIOTool
    - RiskAnalysisTool
  verbose: true

control_designer:
  role: Control Designer
  goal: Design appropriate controls for mitigating each identified risk
  backstory: You are a control framework specialist who develops robust control mechanisms to ensure policy compliance.
  tools:
    - FileIOTool
    - ControlDesignTool
  verbose: true

audit_planner:
  role: Audit Planner
  goal: Create comprehensive test procedures to verify compliance with all conditions
  backstory: You are an experienced compliance auditor who develops thorough audit plans with specific test procedures.
  tools:
    - FileIOTool
    - AuditPlanningTool
  verbose: true
EOL
fi

if [ ! -f config/tasks.yaml ]; then
    echo -e "${YELLOW}Creating default tasks.yaml${NC}"
    cat > config/tasks.yaml << EOL
extract_conditions_task:
  description: |
    Thoroughly analyze ALL preprocessed PDF chunks and extract ALL policy requirements.
    Search for keywords like 'shall', 'should', 'must', 'required', 'obligated' and other modal verbs to extract ALL requirements.
    Ensure COMPLETE coverage by reviewing EVERY document chunk.
    Format the output as a structured list with condition ID, description, and reference (document name, page/section).
    Include the source document name in each reference.
  expected_output: A comprehensive, structured list of all policy compliance conditions with unique IDs, descriptions, and source references including document names.
  agent: policy_analyzer

identify_risks_task:
  description: |
    For each extracted compliance condition, identify and analyze potential risks of non-compliance.
    Assess the likelihood and potential impact of each risk.
    Format the output as a structured list with risk ID, related condition ID, risk description, likelihood, and impact.
    Include references to the source document and page for each risk.
  expected_output: A detailed risk register mapping risks to compliance conditions with assessment of likelihood and impact and source references.
  agent: risk_assessor
  context:
    - extract_conditions_task

design_controls_task:
  description: |
    For each identified risk, design appropriate controls to mitigate the risk and ensure compliance.
    Specify whether each control is preventive, detective, or corrective.
    Format the output as a structured list with control ID, related risk ID, control description, control type, and implementation considerations.
    Include references to the original policy condition's document source and page.
  expected_output: A comprehensive control framework with specific controls mapped to each identified risk and traceability to source documents.
  agent: control_designer
  context:
    - identify_risks_task

develop_tests_task:
  description: |
    For each control, develop detailed test procedures to verify implementation and effectiveness.
    Include specific steps, expected results, and evidence requirements for each test.
    Format the output as a structured audit program with test ID, related control ID, test objective, detailed test steps, and evidence requirements.
    Maintain traceability to the original source documents by including references to document names and page numbers.
  expected_output: A detailed audit program with specific test procedures for each control to verify compliance with policy requirements with source traceability.
  agent: audit_planner
  context:
    - design_controls_task

generate_report_task:
  description: |
    Compile all findings into a comprehensive report that includes:
    1. Executive summary of the policy analysis
    2. Complete listing of all compliance conditions with document sources
    3. Risk assessment results
    4. Control framework
    5. Audit test procedures
    6. Traceability matrix showing relationships between conditions, risks, controls, and tests, including document sources
    Format the report in a professional, well-structured manner suitable for executive review.
    Ensure full traceability to source documents by including document names and page numbers in all references.
  expected_output: A comprehensive compliance analysis report with all components and a traceability matrix that includes source document references.
  agent: policy_analyzer
  context:
    - extract_conditions_task
    - identify_risks_task
    - design_controls_task
    - develop_tests_task
EOL
fi

# Check for policy documents
PDF_COUNT=$(find policy -name "*.pdf" -type f | wc -l)
if [ "$PDF_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}No PDF documents found in the policy directory.${NC}"
    echo -e "${YELLOW}Please add PDF files to the policy directory before proceeding.${NC}"
    
    # Create example file if no documents
    if [ ! -f policy/example_policy.txt ]; then
        echo "Creating example policy file..."
        cat > policy/example_policy.txt << EOL
# Example Policy Document

This is an example policy document. Please replace this with actual PDF policy documents.

## Sample Requirements

1. All employees shall complete security awareness training annually.
2. Passwords must be changed every 90 days.
3. Access to production systems should be reviewed quarterly.
4. Vendors are required to sign NDAs before accessing company data.
5. Security incidents must be reported within 24 hours.
EOL
    fi
else
    echo -e "${GREEN}Found $PDF_COUNT policy documents in the policy directory.${NC}"
fi

# Run document processor
echo -e "${GREEN}Preprocessing documents...${NC}"
python document_processor.py

# Run the main script
echo -e "${GREEN}Running policy compliance analysis...${NC}"
python main.py

# Check for output
if [ -f output/6_final_compliance_report.md ]; then
    echo -e "${GREEN}Analysis completed successfully.${NC}"
    echo -e "${GREEN}Results saved to output/6_final_compliance_report.md${NC}"
else
    echo -e "${RED}Analysis did not complete successfully.${NC}"
    echo -e "${YELLOW}Please check the logs for more information.${NC}"
fi

echo -e "${GREEN}Done.${NC}"
