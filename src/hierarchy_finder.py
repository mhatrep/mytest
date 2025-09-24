import pandas as pd
from collections import defaultdict
from typing import Dict, Any

def build_hierarchies_from_columns(df: pd.DataFrame, parent_col: str, child_col: str) -> Dict[str, Any]:
    """
    Takes a DataFrame and two specified column names (parent and child) and
    builds a hierarchy tree from the data in those columns. This is the final,
    correct implementation for adjacency lists.
    """
    df_copy = df.copy()

    # Normalize the relevant columns to strings
    df_copy[parent_col] = df_copy[parent_col].fillna('').astype(str).str.strip()
    df_copy[child_col] = df_copy[child_col].fillna('').astype(str).str.strip()

    # Build the tree of parent-child relationships
    parent_to_children_map = defaultdict(list)
    all_children = set()

    for _, row in df_copy.iterrows():
        parent, child = row[parent_col], row[child_col]
        if not child:
            continue

        parent_to_children_map[parent].append(child)
        all_children.add(child)

    # Roots are nodes that appear as parents but never as children.
    all_parents = set(parent_to_children_map.keys())
    roots = sorted(list(all_parents - all_children))

    # The dependencies are the unique pairs from the data
    dependencies = sorted(list(set(tuple(row) for row in df_copy[[parent_col, child_col]].values)))

    all_nodes = set(parent_to_children_map.keys()).union(all_children)

    return {
        "dependencies": dependencies,
        "roots": roots,
        "parent_to_children": parent_to_children_map,
        "all_nodes": all_nodes
    }

def format_text_report(analysis_result: Dict[str, Any]) -> str:
    """Formats the hierarchy analysis into a human-readable text report."""
    dependencies = analysis_result["dependencies"]
    roots = analysis_result["roots"]
    parent_to_children = analysis_result["parent_to_children"]

    if not dependencies:
        return "No hierarchical relationships found in the selected columns."

    report_lines = ["Found Hierarchy Chains:\n"]

    def find_chains_recursive(node, current_chain):
        current_chain.append(node)

        children = parent_to_children.get(node, [])

        if not children:
            report_lines.append(" -> ".join(current_chain))
            return

        for child in sorted(children):
            find_chains_recursive(child, list(current_chain))

    if not roots:
        return "No root nodes found (i.e., no items with a blank parent). Cannot determine hierarchies."

    for root in roots:
        find_chains_recursive(root, [])

    return "\n".join(report_lines)

def format_graphviz_dot(analysis_result: Dict[str, Any]) -> str:
    """Formats the hierarchy analysis into a Graphviz .dot file string."""
    dependencies = analysis_result["dependencies"]
    all_nodes = analysis_result["all_nodes"]

    if not dependencies:
        return 'digraph G {\n  label="No hierarchies found";\n}'

    dot_lines = ['digraph G {', '  rankdir=LR;', '  node [shape=box];']
    for node in sorted(list(all_nodes)):
        if node:
            dot_lines.append(f'  "{node}";')

    for parent, child in dependencies:
        if parent and child:
            dot_lines.append(f'  "{parent}" -> "{child}";')

    dot_lines.append('}')
    return "\n".join(dot_lines)

def format_mermaid_js(analysis_result: Dict[str, Any]) -> str:
    """Formats the hierarchy analysis into a Mermaid.js graph string."""
    dependencies = analysis_result["dependencies"]
    if not dependencies:
        return 'graph TD;\n  subgraph No Hierarchies Found\n  end'

    mermaid_lines = ['graph TD;']
    for parent, child in dependencies:
        if parent and child:
            # Sanitize node text for Mermaid.js ID
            parent_id = ''.join(filter(str.isalnum, parent))
            child_id = ''.join(filter(str.isalnum, child))

            # Use a generic ID if sanitization results in an empty string
            if not parent_id: parent_id = f"id_{hash(parent)}"
            if not child_id: child_id = f"id_{hash(child)}"

            mermaid_lines.append(f'  {parent_id}["{parent}"] --> {child_id}["{child}"];')
        elif not parent and child: # Handle root nodes with blank parents
            child_id = ''.join(filter(str.isalnum, child))
            if not child_id: child_id = f"id_{hash(child)}"
            mermaid_lines.append(f'  root["(Root)"] --> {child_id}["{child}"];')

    return "\n".join(mermaid_lines)
