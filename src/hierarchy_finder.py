import pandas as pd
import itertools
from collections import defaultdict

def find_hierarchies(df: pd.DataFrame) -> str:
    """
    Analyzes a DataFrame to find hierarchical relationships between columns.

    A hierarchy B -> A (A is a parent of B) exists if for every value
    of B, there is only one corresponding value of A.

    Returns:
        A formatted string reporting the discovered hierarchies.
    """

    # Treat all data as string to avoid issues with mixed types or NaNs
    df = df.astype(str)

    columns = df.columns
    dependencies = []

    # Check every pair of columns for a functional dependency
    for child_col, parent_col in itertools.permutations(columns, 2):
        # Drop duplicates based on the pair to speed up check
        subset_df = df[[child_col, parent_col]].drop_duplicates()

        # Count how many unique parents each child has
        counts = subset_df.groupby(child_col)[parent_col].nunique()

        # If all children have exactly 1 parent, it's a dependency
        if (counts == 1).all():
            # Further check that the relationship is not 1-to-1
            # A 1-to-1 relationship is not a hierarchy.
            parent_counts = subset_df.groupby(parent_col)[child_col].nunique()
            if not (parent_counts > 1).any():
                # This is a 1-to-1 mapping, not a hierarchy.
                continue

            dependencies.append((parent_col, child_col))

    if not dependencies:
        return "No clear hierarchical relationships found."

    # --- Build a report string and try to chain hierarchies ---
    # Create a graph-like structure
    child_to_parent = dict(reversed(dep) for dep in dependencies)
    parent_to_children = defaultdict(list)
    for parent, child in dependencies:
        parent_to_children[parent].append(child)

    # Find the roots of the hierarchies (nodes that are parents but not children)
    roots = set(parent_to_children.keys()) - set(child_to_parent.keys())

    report_lines = ["Found Hierarchies:\n"]

    # Function to perform a depth-first search to build chain strings
    def find_chains(node, current_chain):
        # Add current node to the chain
        new_chain = current_chain + [node]

        # If this node has no children in our dependency map, we're at the end of a chain
        if node not in parent_to_children:
            report_lines.append(" -> ".join(new_chain))
            return

        # Recurse for all children
        for child in parent_to_children[node]:
            find_chains(child, new_chain)

    if not roots:
        # Handle cases with no clear root or circular dependencies
        report_lines.append("Could not determine hierarchy roots (possible circular dependencies).")
        report_lines.append("\nFound individual parent-child relationships:")
        for parent, child in dependencies:
            report_lines.append(f"- {parent} -> {child}")
    else:
        # Build chains starting from each root
        for root in sorted(list(roots)):
            find_chains(root, [])

    return "\n".join(report_lines)
