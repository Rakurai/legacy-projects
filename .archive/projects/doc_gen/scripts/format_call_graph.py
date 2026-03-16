import sys
from pathlib import Path
import networkx as nx
from colorama import Fore, Style, init
from collections import OrderedDict

# Initialize colorama
init(autoreset=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = PROJECT_ROOT / ".ai/context/internal"
call_graph_path = STATIC_DIR / "code_graph.gml"

# Load the GML call graph
try:
    call_graph = nx.read_gml(call_graph_path)
    print(f"Successfully loaded graph with {len(call_graph.nodes)} nodes and {len(call_graph.edges)} edges")
except Exception as e:
    print(f"Error loading graph: {e}")
    sys.exit(1)

# Define a set of colors to cycle through
COLOR_CYCLE = [
    Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE
]

# Assign a consistent color to each kind/type
color_map = {
    'enum': Fore.MAGENTA,
    'struct': Fore.CYAN,
    'enumvalue': Fore.YELLOW,
    'define': Fore.YELLOW,
    'file': Fore.WHITE,
    'typedef': Fore.YELLOW,
    'namespace': Fore.BLUE,
    'variable': Fore.WHITE,
    'function': Fore.GREEN,
}

def print_dependency_tree(node):
    def _print_tree(n, level=0, visited=None):
        if visited is None:
            visited = set()
        if n in visited:
            print("  " * level + f"{Fore.RED}[CYCLE]{Style.RESET_ALL}")
            return
        visited.add(n)
        attrs = call_graph.nodes[n]
        kind = attrs.get("kind", "unknown")
        name = attrs.get("name", "unknown")
        color = color_map.get(kind, Fore.WHITE)
        print("  " * level + f"{color}{name} [{kind}]{Style.RESET_ALL}")
        for child in call_graph.successors(n):
            _print_tree(child, level + 1, visited.copy())

    _print_tree(node)
def main():
    for n, d in call_graph.nodes(data=True):
        if d['type'] == 'compound':
            print_dependency_tree(n)

if __name__ == "__main__":
    main()
