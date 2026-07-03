import os 
import json
import zipfile
import subprocess
from markitdown import MarkItDown
from openpyxl import Workbook

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

TOOL_REGISTRY = {
    "read_office_file": read_office_file,
    "unpack_raw_xml": unpack_raw_xml,
    "create_xlsx_with_formulas": create_xlsx_with_formulas,
    "execute_shell_command": execute_shell_command
}
