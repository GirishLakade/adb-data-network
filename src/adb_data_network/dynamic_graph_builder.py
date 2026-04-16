from scipy.cluster.hierarchy import ward
import json 
import streamlit as st

def build_d3_graph_from_genie(space_data):
    """
    Parses a Databricks AI/BI Genie Space JSON export and builds 
    a D3-compatible nodes and links dictionary using heuristic matching.
    """
    # 1. Safely load the JSON string if it's not already a dictionary
    if isinstance(space_data, str):
        try:
            data = json.loads(space_data)
        except json.JSONDecodeError:
            return {"nodes": [], "links": []}
    else:
        data = space_data

    nodes = []
    links = []

    # Extract Serialized space
    serialized_space = json.loads(data.get("serialized_space", {}))
    st.write(serialized_space)
    if not serialized_space:
        raise Warning("No serialized space found in the data")
        return serialized_space


    # Extract tables from the nested JSON structure
    tables = serialized_space.get("data_sources", {}).get("tables", [])
    if not tables:
        return {"nodes": nodes, "links": links}

    table_ids = [t["identifier"] for t in tables]
    
    # Categorization lists for relationship building
    fact_tables = []
    dim_tables = []
    other_tables = []

    # ---------------------------------------------------------
    # STEP 1: Build Nodes and Assign Groups
    # ---------------------------------------------------------
    for t_id in table_ids:
        # Extract just the table name (e.g., 'sales_transactions')
        table_name = t_id.split(".")[-1].lower()
        
        # Group 1: Fact Tables (Central hub)
        if "transaction" in table_name or "fact" in table_name:
            group = 1
            fact_tables.append(t_id)
            
        # Group 2: Dimension Tables
        elif any(keyword in table_name for keyword in ["customer", "supplier", "franchise", "dim", "employee", "prospect"]):
            group = 2
            dim_tables.append(t_id)
            
        # Group 3: Media / Supporting Tables
        else:
            group = 3
            other_tables.append(t_id)
            
        nodes.append({"id": t_id, "group": group})

    # ---------------------------------------------------------
    # STEP 2: Build Links (Infer Relationships)
    # ---------------------------------------------------------
    
    # Logic A: Connect Dimension tables to the primary Fact table
    if fact_tables:
        # Default to the first fact table as the center of the star schema
        primary_fact = fact_tables[0] 
        
        for dim in dim_tables:
            # Optional: Ensure they belong to the same schema/domain before linking
            domain_fact = primary_fact.split(".")[1] if len(primary_fact.split(".")) > 1 else ""
            domain_dim = dim.split(".")[1] if len(dim.split(".")) > 1 else ""
            
            if domain_fact == domain_dim:
                links.append({"source": primary_fact, "target": dim})

    # Logic B: Connect supporting/media tables to logical parents
    for other in other_tables:
        if "media" in other:
            if "chunked" in other:
                # Link 'chunked' to the main review table
                parent_review = next((t for t in table_ids if "media_customer_reviews" in t), None)
                if parent_review:
                    links.append({"source": other, "target": parent_review})
            else:
                # Link reviews to customers
                target_cust = next((t for t in dim_tables if "customer" in t), None)
                if target_cust:
                    links.append({"source": other, "target": target_cust})

    return {"nodes": nodes, "links": links}