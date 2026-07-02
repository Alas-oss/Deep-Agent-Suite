import os 
import json
import zipfile
from markitdown import MarkItDown
from openpyxl import Workbook

md_converter = MarkItDown()

def read_office_file(filepath: str) -> str:
    print(f"Processing: {filepath}")
    if not os.path.exists(filepath):
        return f"Error: Target file '{filepath}' not found on the local filesystem."
    try:
        result = md_converter.convert(filepath)
        return result.text_content
    except Exception as e:
        return f"MarkItDown extraction failed: {str(e)}"
    
def unpack_raw_xml(filepath: str, output_dir: str) -> str:
    print(f"Extracting zip layer: '{filepath}' -> '{output_dir}'")
    if not os.path.exists(filepath):
        return f"Error: Source file '{filepath}' missing."
    try: 
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        return f"Successfully unzipped OpenXML structural layout folders into '{output_dir}'."
    except Exception as e:
        return f"Unpack sequence failed: {str(e)}"
    
def create_xlsx_with_formulas(filepath: str, json_data_matrix: str) -> str:
    print(f"Writing spreadsheet data matrix to: {filepath}")
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
        return f"Excel spreadsheet saved with {len(rows)} data rows mapped successfully."
    except Exception as e:
        return f"Excelt compilation failed: {str(e)}"
    
TOOL_REGISTRY = {
    "read_office_file": read_office_file,
    "unpack_raw_xml": unpack_raw_xml,
    "create_xlsx_with_formulas": create_xlsx_with_formulas
}