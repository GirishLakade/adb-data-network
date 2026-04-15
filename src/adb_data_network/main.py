import streamlit as st
import streamlit.components.v1 as components

# 1. Define the Dialog (Pop-up)
# We set width to "large" so it fills a good portion of the center screen
@st.dialog("Interactive Space Relationship Diagram", width="large")
def show_d3_popup(data_nodes):
    st.write("Interactively explore the space IDs and relationships below.")
    
    # This is where your fluid D3.js code lives
    # I'm using a Force-Directed Graph as an example (very 'fluid')
    d3_code = f"""
    <div id="d3-container"></div>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        const data = {data_nodes};
        const width = 800;
        const height = 400;

        const svg = d3.select("#d3-container").append("svg")
            .attr("width", "100%")
            .attr("height", height)
            .attr("viewBox", [0, 0, width, height]);

        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-100))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .attr("stroke", "#999")
            .selectAll("line")
            .data(data.links)
            .join("line");

        const node = svg.append("g")
            .attr("stroke", "#fff")
            .selectAll("circle")
            .data(data.nodes)
            .join("circle")
            .attr("r", 10)
            .attr("fill", d => d.group === 1 ? "#007bff" : "#28a745")
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

        node.append("title").text(d => d.id);

        simulation.on("tick", () => {{
            link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
            node.attr("cx", d => d.x).attr("cy", d => d.y);
        }});
    </script>
    <style>
        #d3-container {{ border: 1px solid #ddd; background: #f9f9f9; border-radius: 8px; }}
    </style>
    """
    
    # Render the D3 inside the popup
    components.html(d3_code, height=450)
    
    if st.button("Done"):
        st.rerun()

# 2. Main Chatbot UI
st.title("Beacon AI: Wealth Management Analytics")

# Mock data for your Space IDs
sample_data = {
    "nodes": [{"id": "Space_Alpha", "group": 1}, {"id": "Space_Beta", "group": 1}, {"id": "Asset_001", "group": 2}],
    "links": [{"source": "Space_Alpha", "target": "Asset_001"}]
}

if st.button("Analyze Space Relationships"):
    show_d3_popup(sample_data)