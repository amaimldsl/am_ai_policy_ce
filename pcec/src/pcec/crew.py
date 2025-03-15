from crewai import Agent, Task, Crew, Process
from crewai import LLM
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Import your custom tools here
from tools.PDFTool import PDFTool

# Load environment variables
load_dotenv()

# Create output directory if it doesn't exist
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

# Get DeepSeek API credentials
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_api_base = os.getenv("DEEPSEEK_API_BASE")
deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat")

# Function to load config from YAML files - Fixed for direct configuration
def load_yaml_config(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Warning: Config file not found at {file_path}. Using hard-coded configuration.")
        return None

# Initialize the DeepSeek LLM with optimal settings for large documents
# In crew.py - Increase token limits
llm = LLM(
    model=deepseek_model,
    api_key=deepseek_api_key,
    api_base=deepseek_api_base,
    temperature=0.2,
    max_tokens=8192,  # Increased from 4096
    streaming=True
)

# Create a separate LLM config with lower token limits for simpler tasks
summarization_llm = LLM(
    model=deepseek_model,
    api_key=deepseek_api_key,
    api_base=deepseek_api_base,
    temperature=0.1,
    max_tokens=4096,  # Increased from 2048
    streaming=True
)
# Try to load agent configurations from YAML
agents_config_path = Path(__file__).parent / "agents.yaml"
tasks_config_path = Path(__file__).parent / "tasks.yaml"

agents_config = load_yaml_config(agents_config_path)
tasks_config = load_yaml_config(tasks_config_path)

# Create PDF Tool with enhanced capabilities
pdf_tool = PDFTool()

# Define agent configs directly if YAML loading fails
if agents_config is None:
    # Hardcoded agent configurations as fallback
    policy_analyzer_config = {
        "role": "Policy Analyzer",
        "goal": "Extract all policy compliance conditions, requirements, and obligations from the PDF",
        "backstory": "You are an expert in policy analysis with experience in regulatory frameworks and compliance requirements extraction."
    }
    
    risk_assessor_config = {
        "role": "Risk Assessor",
        "goal": "Identify and categorize all potential risks associated with each compliance condition",
        "backstory": "You are a risk management professional who specializes in identifying compliance-related risks and their potential impacts."
    }
    
    control_designer_config = {
        "role": "Control Designer",
        "goal": "Design appropriate controls for mitigating each identified risk",
        "backstory": "You are a control framework specialist who develops robust control mechanisms to ensure policy compliance."
    }
    
    audit_planner_config = {
        "role": "Audit Planner",
        "goal": "Create comprehensive test procedures to verify compliance with all conditions",
        "backstory": "You are an experienced compliance auditor who develops thorough audit plans with specific test procedures."
    }
else:
    policy_analyzer_config = agents_config["policy_analyzer"]
    risk_assessor_config = agents_config["risk_assessor"]
    control_designer_config = agents_config["control_designer"]
    audit_planner_config = agents_config["audit_planner"]

# Define enhanced agents with more specific roles and goals
policy_analyzer = Agent(
    role=policy_analyzer_config["role"],
    goal=policy_analyzer_config["goal"],
    backstory=policy_analyzer_config["backstory"],
    tools=[pdf_tool],
    llm=llm,
    verbose=True
)

risk_assessor = Agent(
    role=risk_assessor_config["role"],
    goal=risk_assessor_config["goal"],
    backstory=risk_assessor_config["backstory"],
    tools=[pdf_tool],
    llm=llm,
    verbose=True
)

control_designer = Agent(
    role=control_designer_config["role"],
    goal=control_designer_config["goal"],
    backstory=control_designer_config["backstory"],
    tools=[pdf_tool],
    llm=summarization_llm,  # Using smaller token model for this task
    verbose=True
)

audit_planner = Agent(
    role=audit_planner_config["role"],
    goal=audit_planner_config["goal"],
    backstory=audit_planner_config["backstory"],
    tools=[pdf_tool],
    llm=summarization_llm,  # Using smaller token model for this task
    verbose=True
)

# Additional agent for preprocessing the document to identify modal verbs
modal_verb_extractor = Agent(
    role="Modal Verb Extractor",
    goal="Extract all sentences containing modal verbs that indicate compliance requirements",
    backstory="You are a specialist in identifying compliance language and extracting policy requirements from complex documents.",
    tools=[pdf_tool],
    llm=llm,
    verbose=True
)



# Define task configurations if YAML loading fails
if tasks_config is None:
    # Hardcode task configurations
    extract_conditions_description = """
    Thoroughly analyze the PDF document and extract ALL policy compliance conditions and requirements.
    Focus on extracting requirements based on these indicators:
    1. Modal verbs: 'shall', 'must', 'should', 'will', 'may not', 'required to', 'obligated to'
    2. Imperative statements: 'ensure that', 'provide', 'maintain', 'establish'
    3. Compliance language: 'comply with', 'in accordance with', 'adherence to'
    4. Prohibition language: 'prohibited from', 'restricted from', 'not permitted to'
    
    Process the document in smaller chunks to avoid token limitations:
    - Process one section at a time
    - For each section, identify all compliance requirements
    - Maintain consistent ID format across sections (e.g., REQ-001, REQ-002)
    
    Format each requirement as:
    - ID: [Unique identifier]
    - Requirement: [Full text of the requirement]
    - Source: [Page/section reference]
    - Type: [Mandatory/Recommended based on language]
    - Modal Verb: [The key modal verb or phrase that indicates this is a requirement]

    IMPORTANT - Status reporting:
    - At the beginning, report how many items you received from the previous task
    - At the end, report how many items you produced for the next task
    - Include a statement confirming you processed ALL items
    """
    
    identify_risks_description = """
    For each extracted compliance condition, identify and analyze potential risks of non-compliance.
    Process the requirements in smaller batches (10-15 at a time) to manage token limitations.
    
    For each requirement:
    1. Identify the primary risk of non-compliance
    2. Identify any secondary risks
    3. Assess likelihood (Low/Medium/High) based on complexity and clarity of the requirement
    4. Assess impact (Low/Medium/High) based on potential consequences of non-compliance
    5. Calculate risk score (1-9) based on likelihood and impact

    Format each risk as:
    - Risk ID: [RISK-xxx]
    - Related Requirement ID: [REQ-xxx]
    - Risk Description: [Clear description of what could go wrong]
    - Likelihood: [Low/Medium/High]
    - Impact: [Low/Medium/High]
    - Risk Score: [Numerical score]
    - Risk Level: [Low/Medium/High based on score]
    
    IMPORTANT - Status reporting:
    - At the beginning, report how many items you received from the previous task
    - At the end, report how many items you produced for the next task
    - Include a statement confirming you processed ALL items
    """
    
    
    design_controls_description = """
    For each identified risk, design appropriate controls to mitigate the risk and ensure compliance.
    Process the risks in smaller batches (10-15 at a time) to manage token limitations.
    
    For each risk:
    1. Design at least one control for each risk type:
       - Preventive: Controls that prevent non-compliance
       - Detective: Controls that detect instances of non-compliance
       - Corrective: Controls that address non-compliance when found
    2. Ensure controls are specific, practical, and measurable
    3. Indicate implementation priority (High/Medium/Low) based on risk level
    
    Format each control as:
    - Control ID: [CTRL-xxx]
    - Related Risk ID: [RISK-xxx]
    - Control Description: [Detailed description of the control]
    - Control Type: [Preventive/Detective/Corrective]
    - Implementation Priority: [High/Medium/Low]
    - Implementation Considerations: [Resources, limitations, dependencies]
    
    IMPORTANT - Status reporting:
    - At the beginning, report how many items you received from the previous task
    - At the end, report how many items you produced for the next task
    - Include a statement confirming you processed ALL items
    """
    
    
    develop_tests_description = """
    For each control, develop detailed test procedures to verify implementation and effectiveness.
    Process the controls in smaller batches (10-15 at a time) to manage token limitations.
    
    For each control:
    1. Develop a primary test procedure that directly verifies the control's effectiveness
    2. Include specific, actionable test steps (not generic steps)
    3. Specify the exact evidence to collect and review
    4. Define clear expected results that indicate compliance
    
    Format each test procedure as:
    - Test ID: [TEST-xxx]
    - Related Control ID: [CTRL-xxx]
    - Test Objective: [Clear statement of what the test aims to verify]
    - Test Frequency: [How often the test should be performed]
    - Prerequisites: [What must be in place before testing]
    - Test Steps: [Numbered, detailed steps to perform]
    - Expected Results: [Specific outcomes that indicate compliance]
    - Evidence Requirements: [Exact documents or artifacts to collect]
    
    IMPORTANT - Status reporting:
    - At the beginning, report how many items you received from the previous task
    - At the end, report how many items you produced for the next task
    - Include a statement confirming you processed ALL items
    """
    
    
    generate_report_description = """
    Compile all findings into a comprehensive report, handling token limitations by:
    1. Processing each section (conditions, risks, controls, tests) separately
    2. Creating an executive summary that highlights key findings only
    3. Including statistical summaries rather than full details where appropriate
    
    The report should include:
    1. Executive summary of the policy analysis
    2. Overview statistics (e.g., number of requirements by type, risk levels distribution)
    3. Top 10 highest risk areas
    4. Top 10 most critical controls
    5. Complete listing of all compliance conditions (as an appendix/attachment)
    6. Traceability matrix showing relationships between conditions, risks, controls, and tests
    
    Format the report in a professional, well-structured manner suitable for executive review.
    
    IMPORTANT - Status reporting:
    - At the beginning, report how many items you received from the previous task
    - At the end, report how many items you produced for the next task
    - Include a statement confirming you processed ALL items
    """
    

else:
    extract_conditions_description = tasks_config["extract_conditions_task"]["description"]
    identify_risks_description = tasks_config["identify_risks_task"]["description"]
    design_controls_description = tasks_config["design_controls_task"]["description"]
    develop_tests_description = tasks_config["develop_tests_task"]["description"]
    generate_report_description = tasks_config["generate_report_task"]["description"]




# Define preprocessing task to identify modal verbs

preprocess_document_task = Task(
    description="""
    Pre-analyze the PDF document and extract all sentences containing modal verbs and compliance indicators.
    IMPORTANT: The document has over 200 pages. Process it in batches of 20 pages at a time to ensure FULL coverage:
    
    1. For each batch, use the PDF tool with these parameters:
       - pdf_path: "document.pdf"
       - query: ""
       - page_range: "1-20" for first batch, "21-40" for second batch, etc.
       - chunk_size: 1000
       - chunk_index: 0
       - find_modal_verbs: true
    
    2. Combine results from all batches
    3. DO NOT STOP until you've processed ALL pages of the document
    
    Focus on finding sentences with:
    - Modal verbs: 'shall', 'must', 'should', 'will'
    - Phrases: 'required to', 'obligated to', 'may not', 'prohibited from'
    - Compliance language: 'comply with', 'in accordance with', 'adherence to'
    """,
    expected_output="A COMPLETE list of ALL sentences containing modal verbs and compliance indicators from ALL pages of the document with page references.",
    agent=modal_verb_extractor,
    output_file=str(output_dir / "0_modal_verb_extraction.md")
)

# Define enhanced tasks with clearer objectives and outputs
extract_conditions_task = Task(
    description="""
    Thoroughly analyze ALL modal verb sentences extracted in the previous task.
    IMPORTANT: Ensure you process EVERY SINGLE requirement identified - do not summarize or skip any.
    
    When using the previous task output:
    1. Carefully review ALL extracted sentences
    2. Convert each one into a properly formatted requirement
    3. Maintain a running count to ensure ALL sentences are processed
    4. If the previous output contains more than 100 items, process them in batches of 50-100
    
    Format each requirement exactly as specified...
    """,
    expected_output="A comprehensive, structured list of ALL policy compliance conditions with unique IDs...",
    agent=policy_analyzer,
    context=[preprocess_document_task],
    output_file=str(output_dir / "1_policy_conditions_extraction.md")
)

identify_risks_task = Task(
    description="""
    For EACH extracted compliance condition, identify and analyze potential risks.
    CRITICAL: Process EVERY SINGLE requirement - do not summarize or skip any conditions.
    
    Process requirements in smaller batches (10-15 at a time) to manage token limitations, but ensure ALL are covered.
    
    For tracking completeness:
    1. Begin by counting the total number of requirements from the previous task
    2. Number your risks to match each requirement (maintain traceability)
    3. At the end, verify you've processed ALL requirements by comparing counts
    
    For each requirement:
    [rest of your original instructions]
    """,
    expected_output="A detailed risk register mapping risks to ALL compliance conditions...",
    agent=risk_assessor,
    context=[extract_conditions_task],
    output_file=str(output_dir / "2_risk_assessment.md")
)

design_controls_task = Task(
    description=design_controls_description,
    expected_output="A comprehensive control framework with specific controls mapped to each identified risk.",
    agent=control_designer,
    context=[identify_risks_task],
    output_file=str(output_dir / "3_control_framework.md")
)

develop_tests_task = Task(
    description=develop_tests_description,
    expected_output="A detailed audit program with specific test procedures for each control to verify compliance with policy requirements.",
    agent=audit_planner,
    context=[design_controls_task],
    output_file=str(output_dir / "4_audit_test_procedures.md")
)

generate_report_task = Task(
    description=generate_report_description,
    expected_output="A comprehensive compliance analysis report with all components and a traceability matrix.",
    agent=policy_analyzer,
    context=[extract_conditions_task, identify_risks_task, design_controls_task, develop_tests_task],
    output_file=str(output_dir / "5_final_compliance_report.md")
)



# Add a verification agent and task
verification_agent = Agent(
    role="Process Verifier",
    goal="Ensure complete processing of all items between tasks",
    backstory="You are a quality control specialist who ensures no information is lost between processing steps.",
    tools=[],
    llm=llm,
    verbose=True
)

verify_extraction_task = Task(
    description="""
    Compare the modal verb extraction output with the policy conditions extraction output.
    1. Count the total sentences in the modal verb extraction
    2. Count the total requirements in the policy conditions extraction
    3. Verify that ALL modal verb sentences have been properly converted to requirements
    4. If any are missing, list them for follow-up
    """,
    expected_output="Verification report confirming complete processing or identifying gaps",
    agent=verification_agent,
    context=[preprocess_document_task , extract_conditions_task],
    output_file=str(output_dir / "verification_extraction.md")
)


# Create enhanced crew with sequential process
enhanced_crew = Crew(
    agents=[modal_verb_extractor, policy_analyzer, risk_assessor, control_designer, audit_planner],
    tasks=[preprocess_document_task, extract_conditions_task, identify_risks_task, design_controls_task, develop_tests_task, generate_report_task],
    process=Process.sequential,
    verbose=True,
)

# Make crew available for import
pcec = enhanced_crew