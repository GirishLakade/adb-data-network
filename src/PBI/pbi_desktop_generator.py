import json
import os
import uuid
import argparse
import sys
import re
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")


try:
    import google.generativeai as genai
except ImportError:
    print("Error: 'google-generativeai' package not found. Please install it using 'pip install google-generativeai'.")
    sys.exit(1)

# Default Power BI types and roles
VISUAL_MAPPINGS = {
    "barChart": {"projections": ["Category", "Values"], "role_map": {"axis": "Category", "value": "Values"}},
    "columnChart": {"projections": ["Category", "Values"], "role_map": {"axis": "Category", "value": "Values"}},
    "lineChart": {"projections": ["Category", "Values"], "role_map": {"axis": "Category", "value": "Values"}},
    "pieChart": {"projections": ["Category", "Values"], "role_map": {"legend": "Category", "values": "Values"}},
    "tableEx": {"projections": ["Values"], "role_map": {"field": "Values"}},
}

def analyze_intent(prompt, sql, api_key):
    """
    Uses Gemini to analyze the user prompt and SQL query to determine the best visual and column mapping.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    system_instruction = (
        "You are a Power BI expert. Your task is to analyze a user prompt and the corresponding SQL query "
        "to determine the ideal Power BI visualization. \n"
        "Return a JSON object exactly in this format:\n"
        "{\n"
        "  \"visualType\": \"barChart\" | \"columnChart\" | \"lineChart\" | \"pieChart\" | \"tableEx\",\n"
        "  \"mappings\": [\n"
        "    { \"columnName\": \"sql_column_name\", \"role\": \"Category\" | \"Values\" }\n"
        "  ]\n"
        "}\n"
        "Note: 'Category' is typically the axis/legend, 'Values' is the numeric data. "
        "For 'tableEx', all columns should have the role 'Values'."
    )
    
    user_input = f"User Prompt: {prompt}\nSQL Query: {sql}"
    
    response = model.generate_content([system_instruction, user_input])
    
    # Extract JSON from response
    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        raise ValueError("Failed to parse Gemini response as JSON.")

def generate_pbip_structure(output_dir, report_name, analysis, sql):
    """
    Creates the directory structure and files for the PBIP project.
    """
    # 1. Create Directories
    report_folder = f"{report_name}.Report"
    dataset_folder = f"{report_name}.Dataset"
    
    os.makedirs(os.path.join(output_dir, report_folder), exist_ok=True)
    os.makedirs(os.path.join(output_dir, dataset_folder), exist_ok=True)
    
    # 2. {ReportName}.pbip (Main Pointer)
    pbip_content = {
        "version": "1.0",
        "settings": {},
        "report": {
            "path": report_folder
        }
    }
    with open(os.path.join(output_dir, f"{report_name}.pbip"), "w") as f:
        json.dump(pbip_content, f, indent=2)
        
    # 3. .Dataset/item.config.json & item.metadata.json
    with open(os.path.join(output_dir, dataset_folder, "item.config.json"), "w") as f:
        json.dump({"version": "1.0"}, f)
    with open(os.path.join(output_dir, dataset_folder, "item.metadata.json"), "w") as f:
        json.dump({"type": "Dataset", "displayName": f"{report_name} Dataset"}, f)

    # 4. .Dataset/definition.bim (The Model)
    # This is a simplified BIM file. In a real scenario, you'd define the Databricks connection here.
    bim_content = {
        "version": "1.0",
        "model": {
            "culture": "en-US",
            "tables": [
                {
                    "name": "GenieResults",
                    "columns": [
                        {"name": m["columnName"], "dataType": "string"} for m in analysis["mappings"]
                    ],
                    "partitions": [
                        {
                            "name": "FirstPartition",
                            "source": {
                                "type": "m",
                                "query": f'# "Genie SQL Results" = {sql}' # Placeholder
                            }
                        }
                    ]
                }
            ]
        }
    }
    with open(os.path.join(output_dir, dataset_folder, "definition.bim"), "w") as f:
        json.dump(bim_content, f, indent=2)

    # 5. .Report/item.config.json & item.metadata.json
    with open(os.path.join(output_dir, report_folder, "item.config.json"), "w") as f:
        json.dump({"version": "1.0"}, f)
    with open(os.path.join(output_dir, report_folder, "item.metadata.json"), "w") as f:
        json.dump({"type": "Report", "displayName": report_name}, f)

    # 6. .Report/definition.pbir (Report Pointer)
    pbir_content = {
        "version": "1.0",
        "datasetReference": {
            "byPath": {
                "path": f"../{dataset_folder}"
            }
        }
    }
    with open(os.path.join(output_dir, report_folder, "definition.pbir"), "w") as f:
        json.dump(pbir_content, f, indent=2)

    # 7. .Report/report.json (The Layout)
    visual_type = analysis["visualType"]
    mappings = analysis["mappings"]
    
    # Build visual config
    projections = {}
    query_metadata_select = []
    
    for m in mappings:
        role = m["role"]
        col = m["columnName"]
        if role not in projections:
            projections[role] = []
        projections[role].append({"queryRef": f"GenieResults.{col}"})
        query_metadata_select.append({"Restatement": col, "Name": f"GenieResults.{col}"})

    visual_config = {
        "singleVisual": {
            "visualType": visual_type,
            "projections": projections
        }
    }
    
    data_transforms = {
        "projectionOrdering": {k: list(range(len(v))) for k, v in projections.items()},
        "queryMetadata": {"Select": query_metadata_select}
    }

    report_json = {
        "config": json.dumps({"version": "5.62", "themeCollection": {"baseTheme": {"name": "CY24SU06", "version": "5.62"}}}, ensure_ascii=False),
        "layoutOptimization": 0,
        "sections": [
            {
                "name": "ReportSection",
                "displayName": "Page 1",
                "filters": "[]",
                "config": "{}",
                "visualContainers": [
                    {
                        "x": 0, "y": 0, "z": 0, "width": 800, "height": 600,
                        "config": json.dumps(visual_config, ensure_ascii=False),
                        "dataTransforms": json.dumps(data_transforms, ensure_ascii=False)
                    }
                ]
            }
        ]
    }
    
    with open(os.path.join(output_dir, report_folder, "report.json"), "w") as f:
        json.dump(report_json, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Generate a Power BI Project (PBIP) file based on SQL and prompt.")
    parser.add_argument("--prompt", required=True, help="Original user prompt")
    parser.add_argument("--sql", required=True, help="SQL query generated by Databricks Genie")
    parser.add_argument("--output", default="GeneratedReport", help="Output directory name")
    parser.add_argument("--api-key", help="Gemini API Key (optional, can use GEMINI_API_KEY env var)")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: API Key is required. Provide it via --api-key or GEMINI_API_KEY environment variable.")
        sys.exit(1)
        
    print(f"--- Analyzing Prompt: '{args.prompt}' ---")
    try:
        analysis = analyze_intent(args.prompt, args.sql, api_key)
        print(f"Choice: {analysis['visualType']} with {len(analysis['mappings'])} mappings.")
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)
        
    print(f"--- Generating PBIP Project in folder: {args.output} ---")
    try:
        generate_pbip_structure(".", args.output, analysis, args.sql)
        print("Success! PBIP created.")
        print(f"Structure:\n - {args.output}.pbip\n - {args.output}.Report/\n - {args.output}.Dataset/")
    except Exception as e:
        print(f"Error during generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
