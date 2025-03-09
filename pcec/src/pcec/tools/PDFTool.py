import pdfplumber
from crewai.tools import BaseTool
from pathlib import Path

class PDFTool(BaseTool):
    name: str = "PDF Extraction Tool"
    description: str = "Extracts text from PDF files and performs searches within the extracted content."

    def _run(self, pdf_path: str, query: str = None) -> str:
        
        base_dir = Path(__file__).resolve().parent  # path to tool.py
        pdf_path = base_dir.parent / 'policy/p.pdf'  # going up one level, then into the data directory
        

        try:
            text = self.extract_text_from_pdf(pdf_path)
            if query:
                return self.search_text(text, query)
            return text
        except Exception as e:
            return f"Error processing PDF: {str(e)}"

    def extract_text_from_pdf(self, pdf_path):
        text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text.strip())
        return "\n".join(text)

    def search_text(self, text, query):
        # Implement your search logic here
        # This is a simple example and might need to be more sophisticated
        return [line for line in text.split('\n') if query.lower() in line.lower()]