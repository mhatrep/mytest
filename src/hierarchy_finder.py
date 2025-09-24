import pandas as pd
import itertools
from collections import defaultdict
from typing import List, Dict, Any, Tuple

def analyze_hierarchies(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes a DataFrame to find hierarchical relationships (functional dependencies).
    Returns a dictionary containing the raw dependency data.
    """
    df = df.astype(str)
    columns = df.columns
    dependencies = []

    for child_col, parent_col in itertools.permutations(columns, 2):
        subset_df = df[[child_col, parent_col]].drop_duplicates()
        counts = subset_df.groupby(child_col)[parent_col].nunique()

        if (counts == 1).all():
            parent_counts = subset_df.groupby(parent_col)[child_col].nunique()
            if not (parent_counts > 1).any():
                continue
            dependencies.append((parent_col, child_col))

    child_to_parent = dict(reversed(dep) for dep in dependencies)
    parent_to_children = defaultdict(list)
    for parent, child in dependencies:
        parent_to_children[parent].append(child)

    roots = sorted(list(set(parent_to_children.keys()) - set(child_to_parent.keys())))

    return {
        "dependencies": dependencies,
        "roots": roots,
        "parent_to_children": parent_to_children
    }

def format_text_report(analysis_result: Dict[str, Any]) -> str:
    """Formats the hierarchy analysis into a human-readable text report."""
    dependencies = analysis_result["dependencies"]
    roots = analysis_result["roots"]
    parent_to_children = analysis_result["parent_to_children"]

    if not dependencies:
        return "No clear hierarchical relationships found."

    report_lines = ["Found Hierarchy Chains:\n"]

    def find_chains(node, current_chain):
        new_chain = current_chain + [node]
        if node not in parent_to_children:
            report_lines.append(" -> ".join(new_chain))
            return
        for child in parent_to_children[node]:
            find_chains(child, new_chain)

    if not roots:
        report_lines.append("Could not determine hierarchy roots (possible circular dependencies).")
        report_lines.append("\nFound individual parent-child relationships:")
        for parent, child in dependencies:
            report_lines.append(f"- {parent} -> {child}")
    else:
        for root in roots:
            find_chains(root, [])

    return "\n".join(report_lines)

def format_graphviz_dot(analysis_result: Dict[str, Any]) -> str:
    """Formats the hierarchy analysis into a Graphviz .dot file string."""
    dependencies = analysis_result["dependencies"]
    if not dependencies:
        return 'digraph G {\n  label="No hierarchies found";\n}'

    dot_lines = ['digraph G {', '  rankdir=LR;']
    nodes = set()
    for parent, child in dependencies:
        nodes.add(parent)
        nodes.add(child)
        dot_lines.append(f'  "{parent}" -> "{child}";')

    for node in sorted(list(nodes)):
         dot_lines.append(f'  "{node}" [shape=box];')

    dot_lines.append('}')
    return "\n".join(dot_lines)

def format_mermaid_js(analysis_result: Dict[str, Any]) -> str:
    """Formats the hierarchy analysis into a Mermaid.js graph string."""
    dependencies = analysis_result["dependencies"]
    if not dependencies:
        return 'graph TD;\n  subgraph No Hierarchies Found\n  end'

    mermaid_lines = ['graph TD;']
    for parent, child in dependencies:
        mermaid_lines.append(f'  {parent}["{parent}"] --> {child}["{child}"];')

    return "\n".join(mermaid_lines)
