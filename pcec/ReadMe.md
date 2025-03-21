# Policy Compliance Evaluation and Control (PCEC) Framework

A comprehensive framework for automating compliance policy analysis, risk assessment, control design, and audit planning.

## Overview

The PCEC Framework automates the entire lifecycle of compliance management:

1. **Policy Analysis**: Extract compliance conditions from policy documents
2. **Risk Assessment**: Identify and prioritize risks associated with each compliance condition
3. **Control Design**: Design appropriate controls to mitigate identified risks
4. **Audit Planning**: Develop test procedures to verify control effectiveness
5. **Reporting**: Generate a comprehensive compliance report with traceability

## Key Features

- **Intelligent Extraction**: Automatically extract compliance conditions from policy documents
- **Risk Categorization**: Categorize and prioritize risks with likelihood and impact assessments
- **Control Framework**: Design appropriate preventive, detective, and corrective controls
- **Audit Program**: Generate comprehensive test procedures for each control
- **Traceability**: Maintain full traceability between policies, risks, controls, and tests
- **Quality Assurance**: Ensure complete, meaningful sentences in all outputs

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/pcec-framework.git
cd pcec-framework
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

1. Place your policy documents in the `policy` directory (PDF or text format)

2. Run the main script:
```bash
python main.py
```

3. Find the outputs in the `output` directory:
   - `1_extract_conditions_task_output.md` - Extracted compliance conditions
   - `2_identify_risks_task_output.md` - Risk assessment results
   - `3_design_controls_task_output.md` - Control framework
   - `4_develop_tests_task_output.md` - Audit test procedures
   - `5_final_compliance_report.md` - Comprehensive compliance report

### Individual Task Execution

You can run individual tasks using the task-helper script:

```bash
python task-helper.py extract  # Extract compliance conditions
python task-helper.py risks    # Perform risk assessment
python task-helper.py controls # Design controls
python task-helper.py tests    # Develop test procedures
python task-helper.py report   # Generate final report
```

### Quality Assurance

To ensure all sentences in your reports are complete and meaningful:

```bash
python fix-report.py
```

This script will automatically find and fix any truncated or incomplete sentences in your final report.

## Directory Structure

```
pcec-framework/
├── policy/               # Place your policy documents here
├── preprocessed/         # Preprocessed document chunks (auto-generated)
├── output/               # Generated reports and analysis outputs
├── tools/                # Tool modules for analysis and processing
├── main.py               # Main execution script
├── crew.py               # Agent orchestration
├── task-helper.py        # Individual task execution
├── document_processor.py # Document preprocessing
├── extract-conditions.py # Condition extraction utility
├── fix-report.py         # Report quality assurance utility
└── README.md             # This documentation
```

## Enhanced Sentence Completion

The framework includes specialized handling for incomplete sentences to ensure all extracted conditions, risks, controls, and test procedures are complete and meaningful. This includes:

- Detection of truncated sentences during extraction
- Intelligent completion based on context and compliance language patterns
- Post-processing verification before final report generation
- Standalone tool to fix reports after generation

## Customization

### Configuration Files

- `agents.yaml`: Define agent roles, goals, and tools
- `tasks.yaml`: Define task workflows and dependencies

### Policy Documents

The framework accepts:
- PDF files (recommended)
- Text files (.txt)

Place these in the `policy` directory before running the framework.

## Troubleshooting

If you encounter issues:

1. Check the log files (`crewai_run.log`, `document_processor.log`)
2. Ensure policy documents are properly formatted
3. Run individual tasks using task-helper to isolate the issue
4. Use the fix-report.py script to address any quality issues in the final report

## License

[MIT License](LICENSE)

## Contributors

- Your Name - Initial development
