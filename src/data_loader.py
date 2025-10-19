import json
import yaml
import pandas as pd
from lxml import etree

def find_all_lists(data, path='', results=None):
    """
    Recursively finds all lists of dictionaries in the data and returns them
    with their corresponding paths.
    """
    if results is None:
        results = {}

    if isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{path}.{k}" if path else k
            find_all_lists(v, new_path, results)
    elif isinstance(data, list) and all(isinstance(i, dict) for i in data):
        if not path:
             path = "root"
        results[path] = data
        # Once we've identified a list of dicts, we don't need to recurse further into it
        # for the purpose of finding more tables.

    return results

def load_data(file_path):
    """
    Loads data from a file, supporting JSON, YAML, and XML formats.
    Returns a dictionary of pandas DataFrames, where keys are the paths to the lists.
    """
    raw_data = None
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path, 'r') as f:
            raw_data = yaml.safe_load(f)
    elif file_path.endswith('.xml'):
        try:
            # For XML, we'll let pandas do the heavy lifting
            df = pd.read_xml(file_path)
            return {'root': df}
        except Exception:
            tree = etree.parse(file_path)
            raw_data = etree_to_dict(tree.getroot())
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    all_lists = find_all_lists(raw_data)
    return {path: pd.DataFrame(data) for path, data in all_lists.items()}

def etree_to_dict(t):
    """
    Converts an lxml etree to a dictionary.
    """
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = {}
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                if k in dd:
                    if not isinstance(dd[k], list):
                        dd[k] = [dd[k]]
                    dd[k].append(v)
                else:
                    dd[k] = v
        d = {t.tag: dd}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text and t.text.strip():
        text = t.text.strip()
        if children or t.attrib:
            d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d