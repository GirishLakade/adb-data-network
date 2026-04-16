import streamlit as st
import streamlit.components.v1 as components
import json
from adb_api import GenieAPI   
from dynamic_graph_builder import build_d3_graph_from_genie
from dotenv import load_dotenv
import os


# Get environment variables
load_dotenv()
api_key = os.getenv("ADB_PAT")
instance_url = os.getenv("ADB_INSTANCE_URL")

# 1. Define the Dialog (Pop-up)
@st.dialog("Bakehouse Data Model Explorer", width="large")
def show_d3_popup(data_dict):
    st.write("Interactive view of the Bakehouse Sales data model. Drag the nodes to explore relationships.")
    
    # Convert Python dictionary to JSON string for the Javascript injection
    data_json = json.dumps(data_dict)
    
    # Enhanced D3.js code with visible text labels
    d3_code = f"""
    <div id="d3-container"></div>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        const data = {data_json};
        const width = 800;
        const height = 500;

        const svg = d3.select("#d3-container").append("svg")
            .attr("width", "100%")
            .attr("height", height)
            .attr("viewBox", [0, 0, width, height]);

        // Adjust link distance so table names don't overlap as much
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 2)
            .selectAll("line")
            .data(data.links)
            .join("line");

        // Create groups for nodes so we can append both circles and text
        const node = svg.append("g")
            .selectAll("g")
            .data(data.nodes)
            .join("g")
            .call(d3.drag()
                .on("start", (event, d) => {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x; d.fy = d.y;
                }})
                .on("drag", (event, d) => {{ d.fx = event.x; d.fy = event.y; }})
                .on("end", (event, d) => {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null; d.fy = null;
                }}));

        // Color coding based on groups (1: Fact, 2: Dimension, 3: Media)
        node.append("circle")
            .attr("r", 12)
            .attr("fill", d => {{
                if(d.group === 1) return "#d9534f"; // Red for Transactions
                if(d.group === 2) return "#5bc0de"; // Blue for Sales Dims
                return "#f0ad4e"; // Yellow/Orange for Media
            }})
            .attr("stroke", "#fff")
            .attr("stroke-width", 2);

        // Add table names as visible text
        node.append("text")
            .text(d => d.id.split('.').pop()) // Only show the table name, hide 'samples.bakehouse.'
            .attr("x", 18)
            .attr("y", 4)
            .style("font-family", "sans-serif")
            .style("font-size", "14px")
            .style("fill", "#333")
            .style("pointer-events", "none"); // Prevents text from interfering with drag

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});
    </script>
    <style>
        #d3-container {{ border: 1px solid #ddd; background: #fdfdfd; border-radius: 8px; overflow: hidden; }}
    </style>
    """
    
    # Render the HTML component
    components.html(d3_code, height=550)
    
    if st.button("Close Explorer"):
        st.rerun()

# 2. Main UI Logic
st.title("WMA Analytics Hub")

# The data extracted from your JSON payload
adb_instance=GenieAPI(instance_url, api_key)
space_id = "01f0536b342c1fd9acf8b1800cfefcc8"
bakehouse_data = build_d3_graph_from_genie(adb_instance.get_space_details(space_id))
st.write(bakehouse_data)

if st.button("View Bakehouse Data Model"):
    show_d3_popup(bakehouse_data)