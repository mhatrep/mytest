import pandas as pd
from collections import defaultdict

def find_hierarchies_from_adjacency_list(df: pd.DataFrame) -> str:
    """
    Analyzes a two-column DataFrame representing a parent-child adjacency list
    and reconstructs the full hierarchies.

    Args:
        df (pd.DataFrame): A DataFrame with exactly two columns, assumed to be
                           [parent, child].

    Returns:
        A formatted string reporting the discovered hierarchies.
    """
    if df.shape[1] != 2:
        return (
            "Error: This function requires a file with exactly two columns "
            "representing a parent-child list."
        )

    parent_col, child_col = df.columns[0], df.columns[1]

    # Pre-process data: treat all as strings and handle blanks/NaNs
    df[parent_col] = df[parent_col].fillna('').astype(str)
    df[child_col] = df[child_col].fillna('').astype(str)

    # Build the tree of parent-child relationships
    parent_to_children = defaultdict(list)
    for _, row in df.iterrows():
        parent, child = row[parent_col].strip(), row[child_col].strip()
        if parent and child:
            parent_to_children[parent].append(child)
        # Also capture root nodes that have a blank parent
        elif not parent and child:
            parent_to_children['__ROOT__'].append(child)

    if '__ROOT__' not in parent_to_children:
        return "No root nodes found (i.e., no items with a blank parent). Cannot determine hierarchies."

    report_lines = ["Found Hierarchy Chains:\n"]

    # Function to perform a depth-first search to build chain strings
    def find_chains(node, current_chain):
        current_chain.append(node)

        children = parent_to_children.get(node, [])

        # If this node has no children, we're at the end of a chain
        if not children:
            report_lines.append(" -> ".join(current_chain))
            return

        # Recurse for all children
        for child in sorted(children):
            find_chains(child, list(current_chain))

    # Build chains starting from each root-level node
    for root_node in sorted(parent_to_children['__ROOT__']):
        find_chains(root_node, [])

    return "\n".join(report_lines)
