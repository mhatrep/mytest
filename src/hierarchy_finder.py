import pandas as pd
from collections import defaultdict
from typing import Dict, Any

def build_hierarchies_from_columns(df: pd.DataFrame, parent_col: str, child_col: str) -> Dict[str, Any]:
    """
    Takes a DataFrame and two specified column names (parent and child) and
    builds a hierarchy tree from the data in those columns.
    """
    df_copy = df.copy()

    # Normalize the relevant columns to strings
    df_copy[parent_col] = df_copy[parent_col].fillna('').astype(str).str.strip()
    df_copy[child_col] = df_copy[child_col].fillna('').astype(str).str.strip()

    # Build the tree of parent-child relationships from the specified columns
    parent_to_children_map = defaultdict(list)
    all_children = set()

    for _, row in df_copy.iterrows():
        parent, child = row[parent_col], row[child_col]
        # A blank child name is not a valid node
        if not child:
            continue

        parent_to_children_map[parent].append(child)
        all_children.add(child)

    # Roots are parents that are never themselves a child in any relationship
    # This includes the special '' parent for top-level nodes
    all_parents = set(parent_to_children_map.keys())
    roots = sorted(list(all_parents - all_children))

    # The dependencies are simply the unique pairs from the data
    dependencies = sorted(list(set(tuple(row) for row in df_copy[[parent_col, child_col]].values)))

    all_nodes = all_parents.union(all_children)

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
        # Don't include the artificial blank root in the display
        if node:
            current_chain.append(node)

        children = parent_to_children.get(node, [])

        # If this node has no children, we're at the end of a chain
        if not children:
            if current_chain:
                report_lines.append(" -> ".join(current_chain))
            return

        for child in sorted(children):
            find_chains_recursive(child, list(current_chain))

    if not roots:
        return "Could not determine hierarchy roots (possible circular dependencies)."

    for root in roots:
        # If the root is the blank parent, start traversal from its children
        if root == '':
            for child_node in sorted(parent_to_children.get('', [])):
                find_chains_recursive(child_node, [])
        else:
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
        if node: # Don't draw the artificial blank root
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
            # Sanitize node text for Mermaid.js ID and label
            parent_id = ''.join(filter(str.isalnum, parent))
            child_id = ''.join(filter(str.isalnum, child))
            if not parent_id: parent_id = "blank"
            if not child_id: child_id = "blank"
            mermaid_lines.append(f'  {parent_id}["{parent}"] --> {child_id}["{child}"];')

    return "\n".join(mermaid_lines)
