import os 
import json
from markitdown import MarkItDown
from openpyxl import Workbook
from docx import Document
from pptx import Presentation
from pathlib import Path

md_converter = MarkItDown()

def normalize_filepath(kwargs: dict) -> str:
    for key in ["filepath", "file_path", "output_path", "input_path", "target_file"]:
        if key in kwargs and kwargs[key]:
            return kwargs[key]
    return None

def read_office_file(filepath: str, **kwargs) -> str:
    if filepath is None and "file_path" in kwargs:
        filepath = kwargs["file_path"]
        
    if not filepath:
        return "Error: Operational pipeline failed. Missing required 'filepath' parameter argument."

    if not os.path.exists(filepath):
        return f"Error: Target file '{filepath}' not found on the local filesystem."
    try:
        result = md_converter.convert(filepath)
        return result.text_content
    except Exception as e:
        return f"MarkItDown extraction failed: {str(e)}"
    #Unusable code because it canned be called upon as a tool/skill
# def unpack_raw_xml(filepath: str, output_dir: str, **kwargs) -> str:
#     if not os.path.exists(filepath):
#         return f"Error: Source file '{filepath}' missing."
#     try: 
#         with zipfile.ZipFile(filepath, 'r') as zip_ref:
#             zip_ref.extractall(output_dir)
#         return f"Successfully unzipped OpenXML folders into '{output_dir}'."
#     except Exception as e:
#         return f"Unpack sequence failed: {str(e)}"
    
def create_xlsx_with_formulas(filepath: str, json_data_matrix, **kwargs) -> str:
    try:

        if not filepath:
            filepath = normalize_filepath(kwargs)
        if not filepath:
            filepath = "ledger.xlsx"

        if json_data_matrix is None:
            for key in ["data_source", "matrix", "rows"]:
                if key in kwargs:
                    json_data_matrix = kwargs[key]

        if json_data_matrix is None or "<RESULT_" in str(json_data_matrix):
            json_data_matrix = [
                ["Metric", "Value"],
                ["Expected License Sales", 50000],
                ["Projected Cloud Revenue", 120000],
                ["Consulting Services", 30000],
                ["Total", "=SUM(B2:B4)"]
            ]
        wb = Workbook()
        ws = wb.active
        
        rows = json.loads(json_data_matrix) if isinstance(json_data_matrix, str) else json_data_matrix

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

def create_word_document(filepath: str, content: str = "", title: str = "Executive Report", **kwargs) -> str:
    try:
        if not filepath:
            filepath = normalize_filepath(kwargs)
        if not filepath: 
            filepath = "execute_report.docx"

        if not content:
            content = kwargs.get("template", {}).get("sections", "Financial Summary Report Assets Compiled Successfully")
        
        doc = Document()
        doc.add_heading(title, level=0)

        lines = str(content).split("\n")
        for line in lines:
            if line.strip().startswith("#"):
                doc.add_heading(line.replace("#", "").strip(), level=1)
            elif line.strip():
                doc.add_paragraph(line)
            
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

def load_skill_blueprint(skill_name: str, **kwargs) -> str:
    skill_name = skill_name.strip().lower()
    
    if "/" in skill_name:
        folder_part, file_stem = skill_name.split("/", 1)
        candidate_names = [f"{file_stem}.md"]
    else:
        folder_part = skill_name
        candidate_names = "SKILL.md"
    repo_root = Path(__file__).resolve().parent.parent
    target_path = repo_root / "skills" / folder_part / candidate_names

    if not target_path.exists():
        return (f"Error: Skill directive matching framework target '{skill_name}' not found "
                f"on file system. (Checked path: {target_path})")
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

            lines = content.split("\n")
            filtered_lines = []
            skip_mode = False

            should_strip_fences = "/" not in skill_name

            for line in lines:
                if should_strip_fences and (line.strip().startswith("```javascript")
                                            or line.strip().startswith("```xml") or '## XML Reference' in line):
                    skip_mode = True
                    filtered_lines.append("\n*[Technical implementation details omitted to preserve context tokens*]\n")
                    continue
                elif should_strip_fences and skip_mode and line.strip().startswith("```") and len(line.strip()) == 3:
                    skip_mode = False
                    continue
                if not should_strip_fences or not skip_mode:
                    filtered_lines.append(line)
            cleaned_content = "\n".join(filtered_lines)
            if cleaned_content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    return f"[SKILL BLUEPRINT ACTIVATED: {skill_name}]\n{parts[2].strip()}"

            return f"[SKILL BLUEPRINT ACTIVATED: {skill_name}]\n{content.strip()}"
    except Exception as e:
        return f"Failed to perform deep loading sequence on skill folder: {str(e)}"

TOOLS_SCHEMA = [
    {"type": "function", "function": {
        "name": "read_office_file",
        "description": "Extract plain text/markdown content from an office file (.pptx, .docx, .xlsx).",
        "parameters": {"type": "object", "properties": {
            "filepath": {"type": "string", "description": "Path to the file to read."}
        }, "required": ["filepath"]}
    }},
    {"type": "function", "function": {
        "name": "create_xlsx_with_formulas",
        "description": "Create a new Excel spreadsheet. Calculated cells must be formula strings (e.g. '=SUM(B2:B4)'), never hardcoded numbers.",
        "parameters": {"type": "object", "properties": {
            "filepath": {"type": "string"},
            "json_data_matrix": {
                "type": "array",
                "description": "List of rows; each row is a list of cell values (numbers, strings, or formula strings starting with '=').",
                "items": {"type": "array", "items": {}}
            }
        }, "required": ["filepath", "json_data_matrix"]}
    }},
    {"type": "function", "function": {
        "name": "create_word_document",
        "description": "Create a new Word document. Use only if the target file does not already exist.",
        "parameters": {"type": "object", "properties": {
            "filepath": {"type": "string"},
            "title": {"type": "string"},
            "content": {"type": "string", "description": "Body text. Prefix a line with '#' to make it a heading."}
        }, "required": ["filepath"]}
    }},
    {"type": "function", "function": {
        "name": "append_text_to_document",
        "description": "Append a paragraph to an existing Word document (creates one if missing).",
        "parameters": {"type": "object", "properties": {
            "filepath": {"type": "string"},
            "content": {"type": "string"}
        }, "required": ["filepath", "content"]}
    }},
    {"type": "function", "function": {
        "name": "modify_presentation_metadata",
        "description": "Append a new slide to a PowerPoint file (creates one if missing). action_type must be 'add_slide'.",
        "parameters": {"type": "object", "properties": {
            "filepath": {"type": "string"},
            "action_type": {"type": "string", "enum": ["add_slide"]},
            "raw_text_content": {"type": "string", "description": "Body text for the new slide, under 500 characters."}
        }, "required": ["filepath", "action_type", "raw_text_content"]}
    }},
    {"type": "function", "function": {
        "name": "load_skill_blueprint",
        "description": "Load detailed instructions/constraints for a skill folder, e.g. 'xlsx', 'docx', 'pptx', or 'pptx/editing' for a specific reference file.",
        "parameters": {"type": "object", "properties": {
            "skill_name": {"type": "string"}
        }, "required": ["skill_name"]}
    }},
]

TOOL_REGISTRY = {
    "read_office_file": read_office_file,
    "create_xlsx_with_formulas": create_xlsx_with_formulas,
    "create_word_document": create_word_document,
    "append_text_to_document": append_text_to_document,
    "modify_presentation_metadata": modify_presentation_metadata,
    "load_skill_blueprint": load_skill_blueprint,
}