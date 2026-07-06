import os 
import json
import zipfile
import subprocess
from markitdown import MarkItDown
from openpyxl import Workbook
from docx import Document
from pptx import Presentation

md_converter = MarkItDown()

def read_office_file(filepath: str, **kwargs) -> str:
    if not os.path.exists(filepath):
        return f"Error: Target file '{filepath}' not found on the local filesystem."
    try:
        result = md_converter.convert(filepath)
        return result.text_content
    except Exception as e:
        return f"MarkItDown extraction failed: {str(e)}"
    
def unpack_raw_xml(filepath: str, output_dir: str, **kwargs) -> str:
    if not os.path.exists(filepath):
        return f"Error: Source file '{filepath}' missing."
    try: 
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        return f"Successfully unzipped OpenXML folders into '{output_dir}'."
    except Exception as e:
        return f"Unpack sequence failed: {str(e)}"
    
def create_xlsx_with_formulas(filepath: str, json_data_matrix, **kwargs) -> str:
    try:
        wb = Workbook()
        ws = wb.active
        
        if isinstance(json_data_matrix, str):
            rows = json.loads(json_data_matrix)
        else:
            rows = json_data_matrix

        for row in rows:
            processed_row = []
            for cell in row:
                if isinstance(cell, dict) and "formula" in cell:
                    processed_row.append(cell["formula"])
                else:
                    processed_row.append(cell)
            ws.append(processed_row)
            
        wb.save(filepath)
        return f"Successfully created Excel spreadsheet at {filepath}."
    except Exception as e:
        return f"Spreadsheet build failed: {str(e)}"

def execute_shell_command(command: str, **kwargs) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        return output if output.strip() else "Command executed successfully with zero terminal output."
    except subprocess.TimeoutExpired:
        return "Error: Execution timed out after 30 seconds."
    except Exception as e:
        return f"Shell execution failed with system exception: {str(e)}"

def create_word_document(filepath: str, content: str = "", title: str = "Executive Report", **kwargs) -> str:
    try:
        doc = Document()
        doc.add_heading(title, level=0)

        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("#"):
                doc.add_heading(line.replace("#", "").strip(), level=1)
            elif line.strip():
                doc.add_paragraph(line)
        # if isinstance(paragraphs, str):
        #     text_blocks = json.loads(paragraphs)
        # else: 
        #     text_blocks = paragraphs

        # for block in text_blocks:
        #     if isinstance(block, dict) and "heading" in block:
        #         doc.add_heading(block["heading"], level=int(block.get("level", 1)))
        #     elif isinstance(block, dict) and "text" in block:
        #         doc.add_paragraph(block["text"])
        #     else:
        #         doc.add_paragraph(str(block))
            
        doc.save(filepath)
        return f"Generated a Microsoft Word narrative file at {filepath}."
    except Exception as e:
        return f"Word document creation failed: {str(e)}"
    
def append_text_to_document(filepath: str, content: str, **kwargs) -> str:
    try:
        if not os.path.exists(filepath):
            doc = Document()
            doc.add_heading("Automated Updates Document log", level=1)
        else:
            doc = Document(filepath)

        doc.add_paragraph(content)
        doc.save(filepath)
        return f"Appended content updates to {filepath}."
    except Exception as e:
        return f"Failed to append content onto text file target: {str(e)}"
    
def modify_presentation_metadata(filepath: str, action_type: str, raw_text_content: str, **kwargs) -> str:
    try:
        if not os.path.exists(filepath):
            pres = Presentation()
        else:
            pres = Presentation(filepath)
        
        if action_type == "add_slide":
            slide = pres.slides.add_slide(pres.slide_layouts[1])
            slide.shapes.title.text = "Automated Agent Update Output"
            body_shape = slide.shapes.placeholders[1]
            body_shape.text = raw_text_content 
        
        pres.save(filepath)
        return f"Modified PowerPoint file structure at {filepath}."
    except Exception as e:
        return f"Presentation pipeline modifications failed: {str(e)}"


TOOL_REGISTRY = {
    "read_office_file": read_office_file,
    "unpack_raw_xml": unpack_raw_xml,
    "create_xlsx_with_formulas": create_xlsx_with_formulas,
    "execute_shell_command": execute_shell_command,
    "create_word_document": create_word_document,
    "append_text_to_document": append_text_to_document,
    "modify_presentation_metadata": modify_presentation_metadata
}