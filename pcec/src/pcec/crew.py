# Enhanced crew.py
from crewai import Agent, Task, Crew, Process
from crewai import LLM
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
import yaml
import re

# Import your custom tools
from tools.PDFTool import PDFTool
from tools.FileIOTool import FileIOTool
from tools.RiskAnalysisTool import RiskAnalysisTool
from tools.ControlDesignTool import ControlDesignTool
from tools.AuditPlanningTool import AuditPlanningTool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crewai_run.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Tool registry for mapping tool names to their classes
TOOL_REGISTRY = {
    "PDFTool": PDFTool,
    "FileIOTool": FileIOTool,
    "RiskAnalysisTool": RiskAnalysisTool,
    "ControlDesignTool": ControlDesignTool,
    "AuditPlanningTool": AuditPlanningTool
}

class CrewBuilder:
    """Centralized crew building with configuration loading from YAML files"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Create output directory if it doesn't exist
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup LLM with error handling
        self.llm = self._setup_llm()
        
        # Load configurations
        self.agents_config = self._load_yaml_config("agents.yaml")
        self.tasks_config = self._load_yaml_config("tasks.yaml")
        
        # Initialize agent and task mappings
        self.agents = {}
        self.tasks = {}
        
        # Initialize the agents and tasks
        self._create_agents()
        self._create_tasks()
    
    def _load_yaml_config(self, filename):
        """Load configuration from YAML file, looking in several possible locations"""
        try:
            # Try multiple possible locations for the config file
            possible_paths = [
                Path(__file__).resolve().parent / filename,                  # Same directory as script
                Path(__file__).resolve().parent / "config" / filename,       # config subdirectory
                Path(__file__).resolve().parent.parent / "config" / filename, # parent/config directory
                Path.cwd() / filename,                                       # Current working directory
                Path.cwd() / "config" / filename,                            # Current working directory /config
                Path.cwd() / "src" / "pcec" / "config" / filename,           # Project structure
            ]
            
            # Try to find and load the file from any of the possible locations
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r') as file:
                        config = yaml.safe_load(file)
                        logger.info(f"Successfully loaded configuration from {path}")
                        return config
            
            # If we get here, we couldn't find the file in any location
            logger.warning(f"Configuration file {filename} not found. Using default configuration.")
            
            # Return default configuration based on filename
            if filename == "agents.yaml":
                return self._default_agents_config()
            elif filename == "tasks.yaml":
                return self._default_tasks_config()
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error loading configuration from {filename}: {str(e)}")
            return {}
    
    def _default_agents_config(self):
        """Return default agent configuration if agents.yaml not found"""
        return {
            "policy_analyzer": {
                "role": "Policy Analyzer",
                "goal": "Extract all policy compliance conditions from documents",
                "backstory": "You are an expert in policy analysis with regulatory experience.",
                "tools": ["PDFTool", "FileIOTool"],
                "verbose": True
            },
            "risk_assessor": {
                "role": "Risk Assessor",
                "goal": "Identify risks associated with compliance conditions",
                "backstory": "You are a risk management professional.",
                "tools": ["FileIOTool", "RiskAnalysisTool"],
                "verbose": True
            },
            "control_designer": {
                "role": "Control Designer",
                "goal": "Design controls for mitigating risks",
                "backstory": "You are a control framework specialist.",
                "tools": ["FileIOTool", "ControlDesignTool"],
                "verbose": True
            },
            "audit_planner": {
                "role": "Audit Planner",
                "goal": "Create test procedures to verify compliance",
                "backstory": "You are an experienced compliance auditor.",
                "tools": ["FileIOTool", "AuditPlanningTool"],
                "verbose": True
            }
        }

    def _default_tasks_config(self):
        """Return default task configuration if tasks.yaml not found"""
        return {
            "list_chunks_task": {
                "description": "List all available preprocessed document chunks.",
                "expected_output": "A list of all preprocessed document chunks available for analysis.",
                "agent": "policy_analyzer"
            },
            "extract_conditions_task": {
                "description": "Extract all policy compliance conditions from preprocessed document chunks.",
                "expected_output": "A consolidated list of all policy compliance conditions from all analyzed chunks.",
                "agent": "policy_analyzer",
                "context": ["list_chunks_task"]
            },
            "identify_risks_task": {
                "description": "Identify and categorize all potential risks associated with each compliance condition.",
                "expected_output": "A comprehensive risk assessment for all compliance conditions.",
                "agent": "risk_assessor",
                "context": ["extract_conditions_task"]
            },
            "design_controls_task": {
                "description": "Design appropriate controls for mitigating each identified risk.",
                "expected_output": "A comprehensive control framework for mitigating all identified risks.",
                "agent": "control_designer",
                "context": ["identify_risks_task"]
            },
            "develop_tests_task": {
                "description": "Develop test procedures for verifying each control.",
                "expected_output": "A comprehensive audit program for verifying all controls.",
                "agent": "audit_planner",
                "context": ["design_controls_task"]
            },
            "generate_report_task": {
                "description": "Compile all findings into a comprehensive report.",
                "expected_output": "A comprehensive compliance analysis report with all components.",
                "agent": "policy_analyzer",
                "context": ["extract_conditions_task", "identify_risks_task", "design_controls_task", "develop_tests_task"]
            }
        }
    
    def _setup_llm(self):
        """Setup the LLM with error handling"""
        try:
            # Get DeepSeek API credentials
            deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
            deepseek_api_base = os.getenv("DEEPSEEK_API_BASE")
            deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat")
            
            # Initialize the DeepSeek LLM with reduced max_tokens
            llm = LLM(
                model=deepseek_model,
                api_key=deepseek_api_key,
                api_base=deepseek_api_base,
                temperature=0.2,
                max_tokens=4096,
                streaming=True,
                custom_llm_provider="deepseek"
            )
            
            # Add error handling for LLM calls
            original_call = llm.call
            
            def safe_llm_call(*args, **kwargs):
                try:
                    return original_call(*args, **kwargs)
                except Exception as e:
                    logger.error(f"LLM call error: {str(e)}")
                    return "Error processing this request. Please try with smaller input or different parameters."
            
            # Override the LLM call method with our safe version
            llm._call = safe_llm_call
            
            return llm
            
        except Exception as e:
            logger.error(f"Error setting up LLM: {str(e)}")
            raise
    
    def _create_agents(self):
        """Create agents from YAML configuration"""
        if not self.agents_config:
            logger.warning("No agent configuration found. Using default agents.")
            self._create_default_agents()
            return
            
        try:
            for agent_name, agent_config in self.agents_config.items():
                tools = []
                
                # Create tools specified in the configuration
                if "tools" in agent_config:
                    for tool_name in agent_config["tools"]:
                        if tool_name in TOOL_REGISTRY:
                            tools.append(TOOL_REGISTRY[tool_name]())
                        else:
                            logger.warning(f"Tool {tool_name} not found in registry. Skipping.")
                
                # Create the agent
                self.agents[agent_name] = Agent(
                    role=agent_config.get("role", f"Generic {agent_name}"),
                    goal=agent_config.get("goal", "Complete assigned tasks effectively"),
                    backstory=agent_config.get("backstory", ""),
                    tools=tools,
                    llm=self.llm,
                    verbose=agent_config.get("verbose", True)
                )
                
                logger.info(f"Created agent: {agent_name}")
                
        except Exception as e:
            logger.error(f"Error creating agents: {str(e)}")
            logger.info("Falling back to default agents")
            self._create_default_agents()
    
    def _create_default_agents(self):
        """Create default agents if configuration fails"""
        self.agents["policy_analyzer"] = Agent(
            role="Policy Analyzer",
            goal="Extract all policy compliance conditions from documents",
            backstory="You are an expert in policy analysis with regulatory experience.",
            tools=[PDFTool(), FileIOTool()],
            llm=self.llm,
            verbose=True
        )
        
        self.agents["risk_assessor"] = Agent(
            role="Risk Assessor",
            goal="Identify risks associated with compliance conditions",
            backstory="You are a risk management professional.",
            tools=[FileIOTool(), RiskAnalysisTool()],
            llm=self.llm,
            verbose=True
        )
        
        self.agents["control_designer"] = Agent(
            role="Control Designer",
            goal="Design controls for mitigating risks",
            backstory="You are a control framework specialist.",
            tools=[FileIOTool(), ControlDesignTool()],
            llm=self.llm,
            verbose=True
        )
        
        self.agents["audit_planner"] = Agent(
            role="Audit Planner",
            goal="Create test procedures to verify compliance",
            backstory="You are an experienced compliance auditor.",
            tools=[FileIOTool(), AuditPlanningTool()],
            llm=self.llm,
            verbose=True
        )
        
        logger.info("Created default agents")
        
    def _create_tasks(self):
        """Create tasks from YAML configuration"""
        if not self.tasks_config:
            logger.warning("No task configuration found. Using default tasks.")
            self._create_default_tasks()
            return
            
        try:
            # Track dependencies between tasks
            task_dependencies = {}
            
            # First pass: create all tasks without dependencies
            for task_name, task_config in self.tasks_config.items():
                # Get the agent for this task
                agent_name = task_config.get("agent")
                if agent_name not in self.agents:
                    logger.warning(f"Agent {agent_name} not found for task {task_name}. Skipping.")
                    continue
                
                # Create the task
                output_file = str(self.output_dir / f"{task_name}_output.md")
                
                self.tasks[task_name] = Task(
                    description=task_config.get("description", f"Task: {task_name}"),
                    expected_output=task_config.get("expected_output", "Completed task output"),
                    agent=self.agents[agent_name],
                    output_file=output_file
                )
                
                # Store context dependencies for second pass
                if "context" in task_config:
                    task_dependencies[task_name] = task_config["context"]
                
                logger.info(f"Created task: {task_name}")
            
            # Second pass: add dependencies
            for task_name, dependencies in task_dependencies.items():
                if task_name in self.tasks:
                    context_tasks = []
                    for dep in dependencies:
                        if dep in self.tasks:
                            context_tasks.append(self.tasks[dep])
                        else:
                            logger.warning(f"Dependency {dep} not found for task {task_name}")
                    
                    # Update the task with context
                    self.tasks[task_name].context = context_tasks
            
        except Exception as e:
            logger.error(f"Error creating tasks: {str(e)}")
            logger.info("Falling back to default tasks")
            self._create_default_tasks()
            
    def _create_default_tasks(self):
        """Create default tasks if configuration fails"""
        # Create default tasks similar to what was in the original crew.py
        self.tasks["list_chunks"] = Task(
            description="List all available preprocessed document chunks.",
            expected_output="A list of all preprocessed document chunks available for analysis.",
            agent=self.agents["policy_analyzer"],
            output_file=str(self.output_dir / "0_chunk_list.md")
        )
        
        # Create tasks for processing first 5 chunks
        chunk_tasks = []
        for i in range(5):
            task = Task(
                description=f"Analyze document chunk with index {i} and extract compliance conditions.",
                expected_output=f"A list of policy compliance conditions extracted from chunk {i}.",
                agent=self.agents["policy_analyzer"],
                context=[self.tasks["list_chunks"]],
                output_file=str(self.output_dir / f"1_conditions_chunk_{i}.md")
            )
            self.tasks[f"process_chunk_{i}"] = task
            chunk_tasks.append(task)
        
        # Create consolidation task
        self.tasks["consolidate_conditions"] = Task(
            description="Consolidate all the conditions extracted from individual chunks.",
            expected_output="A consolidated list of all policy compliance conditions from all analyzed chunks.",
            agent=self.agents["policy_analyzer"],
            context=chunk_tasks,
            output_file=str(self.output_dir / "2_consolidated_conditions.md")
        )
        
        # Create risk assessment task
        self.tasks["risk_assessment"] = Task(
            description="Perform risk assessment on the consolidated conditions list.",
            expected_output="A comprehensive risk assessment for all compliance conditions.",
            agent=self.agents["risk_assessor"],
            context=[self.tasks["consolidate_conditions"]],
            output_file=str(self.output_dir / "3_risk_assessment.md")
        )
        
        # Create control design task
        self.tasks["design_controls"] = Task(
            description="Design appropriate controls for each identified risk.",
            expected_output="A comprehensive control framework for mitigating all identified risks.",
            agent=self.agents["control_designer"],
            context=[self.tasks["risk_assessment"]],
            output_file=str(self.output_dir / "4_control_framework.md")
        )
        
        # Create audit planning task
        self.tasks["develop_tests"] = Task(
            description="Develop test procedures for verifying each control.",
            expected_output="A comprehensive audit program for verifying all controls.",
            agent=self.agents["audit_planner"],
            context=[self.tasks["design_controls"]],
            output_file=str(self.output_dir / "5_audit_program.md")
        )
        
        # Create report generation task
        self.tasks["generate_report"] = Task(
            description="Compile all findings into a comprehensive report.",
            expected_output="A comprehensive compliance analysis report with all components.",
            agent=self.agents["policy_analyzer"],
            context=[
                self.tasks["consolidate_conditions"],
                self.tasks["risk_assessment"],
                self.tasks["design_controls"],
                self.tasks["develop_tests"]
            ],
            output_file=str(self.output_dir / "6_final_compliance_report.md")
        )
        
        logger.info("Created default tasks")
    
    def build_crew(self):
        """Build and return the crew with all agents and tasks"""
        # Convert task dictionary values to a list
        task_list = list(self.tasks.values())
        
        # Create the crew
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=task_list,
            process=Process.sequential,
            verbose=True,
            max_task_errors=3,
            task_timeout=600,
        )
        
        logger.info(f"Built crew with {len(self.agents)} agents and {len(self.tasks)} tasks")
        return crew

# Create the CrewBuilder instance and build the crew
crew_builder = CrewBuilder()
pcec = crew_builder.build_crew()