import json
import logging
import sys
from pathlib import Path

import networkx as nx
from flask import Flask, jsonify, send_from_directory, render_template_string

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = PROJECT_ROOT / ".ai/context/internal"

call_graph_path = STATIC_DIR / "clang_call_graph.json"
web_graph_output = STATIC_DIR / "web_call_graph.json"

# Load the GML call graph
try:
    call_graph = nx.read_gml(call_graph_path)
    print(f"Successfully loaded graph with {len(call_graph.nodes)} nodes and {len(call_graph.edges)} edges")
except Exception as e:
    print(f"Error loading graph: {e}")
    sys.exit(1)

# Convert to Cytoscape.js format
cytoscape_data = {
    "nodes": [],
    "edges": []
}

for node_id, attrs in call_graph.nodes(data=True):
    node_data = {
        "id": str(node_id),
        "label": str(node_id)
    }
    for attr in ['entity_type', 'file', 'line', 'end_line', 'doc_comment']:
        if attr in attrs and attrs[attr]:
            val = attrs[attr]
            if attr == 'doc_comment' and len(val) > 100:
                val = val[:97] + "..."
            node_data[attr] = val
    cytoscape_data["nodes"].append({"data": node_data})

for source, target in call_graph.edges():
    cytoscape_data["edges"].append({
        "data": {
            "id": f"{source}->{target}",
            "source": str(source),
            "target": str(target)
        }
    })

# Write Cytoscape-compatible JSON to disk
with open(web_graph_output, 'w') as f:
    json.dump(cytoscape_data, f, indent=2)

print(f"Web visualization data written to {web_graph_output}")

# Flask app for serving the graph
app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <title>Call Graph Visualization</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.24.0/cytoscape.min.js"></script>
  <style>
    body { font-family: sans-serif; }
    #cy { width: 100vw; height: 95vh; border: 1px solid #ccc; }
  </style>
</head>
<body>
  <h2>Call Graph Viewer</h2>
  <div id="cy"></div>
  <script>
    fetch("/graph-data")
      .then(res => res.json())
      .then(data => {
        const cy = cytoscape({
          container: document.getElementById('cy'),
          elements: data.nodes.concat(data.edges),
          style: [
            {
              selector: 'node',
              style: {
                'label': 'data(label)',
                'background-color': '#0074D9',
                'color': '#fff',
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': 10
              }
            },
            {
              selector: 'edge',
              style: {
                'width': 2,
                'line-color': '#ccc',
                'target-arrow-color': '#ccc',
                'target-arrow-shape': 'triangle'
              }
            }
          ],
          layout: {
            name: 'cose',
            animate: true
          }
        });
      });
  </script>
</body>
</html>
    """)

@app.route("/graph-data")
def graph_data():
    return jsonify(cytoscape_data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)