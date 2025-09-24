import pandas as pd
import itertools
from collections import defaultdict
from typing import List, Dict, Any

def analyze_hierarchies(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes a DataFrame to find hierarchical relationships (functional dependencies)
    by checking all pairs of columns. This is the robust, correct implementation.
    """
    df_copy = df.copy()

    for col in df_copy.columns:
        df_copy[col] = df_copy[col].fillna('').astype(str).str.strip()

    columns = df_copy.columns
    dependencies = []

    for child_col, parent_col in itertools.permutations(columns, 2):
        if child_col == parent_col:
            continue

        subset_df = df_copy[[child_col, parent_col]]
        # A blank child value is not a valid node in a hierarchy
        subset_df = subset_df[subset_df[child_col] != '']

        if subset_df.empty:
            continue

        # A child is dependent on a parent if each child value maps to exactly one parent value.
        # We group by the child and count the number of unique parents.
        # We also drop rows where the parent is blank, as a blank parent isn't a real entity.
        counts = subset_df[subset_df[parent_col] != ''].groupby(child_col)[parent_col].nunique()

        # If the counts series is empty (e.g., all parents were blank), there's no dependency.
        if counts.empty:
            continue

        # If all children have exactly 1 parent, it's a potential dependency
        if (counts == 1).all():
            # To be a hierarchy, the parent must have multiple children for at least one value.
            # Otherwise, it's a 1-to-1 mapping which isn't a hierarchy.
            parent_counts = subset_df.groupby(parent_col)[child_col].nunique()
            if (parent_counts > 1).any():
                dependencies.append((parent_col, child_col))

    # --- Process the found dependencies to build chains ---
    child_to_parent_map = {child: parent for parent, child in dependencies}
    parent_to_children_map = defaultdict(list)
    all_nodes = set()
    for parent, child in dependencies:
        parent_to_children_map[parent].append(child)
        all_nodes.add(parent)
        all_nodes.add(child)

    # Roots are nodes that appear as parents but never as children.
    roots = sorted(list(set(parent_to_children_map.keys()) - set(child_to_parent_map.keys())))

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
        return "No clear hierarchical relationships found."

    report_lines = ["Found Hierarchy Chains:\n"]

    def find_chains_recursive(node, current_chain):
        new_chain = current_chain + [node]
        children = parent_to_children.get(node, [])

        if not children:
            report_lines.append(" -> ".join(new_chain))
            return

        for child in sorted(children):
            find_chains_recursive(child, list(new_chain))

    if not roots:
        report_lines.append("Could not determine hierarchy roots (possible circular dependencies).")
        report_lines.append("\nFound individual parent-child relationships:")
        for parent, child in sorted(dependencies):
            report_lines.append(f"- {parent} -> {child}")
    else:
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
         if node: dot_lines.append(f'  "{node}";')

    for parent, child in dependencies:
        if parent and child: dot_lines.append(f'  "{parent}" -> "{child}";')

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
