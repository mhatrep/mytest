import json
import yaml
import pandas as pd
from lxml import etree

def find_list_for_dataframe(data):
    """
    Finds the best list within the data to convert to a DataFrame.
    It prioritizes lists of dictionaries.
    If the root is a dictionary with a single list, it returns that list.
    """
    if isinstance(data, list) and all(isinstance(i, dict) for i in data):
        return data

    if isinstance(data, dict):
        list_values = [v for v in data.values() if isinstance(v, list) and all(isinstance(i, dict) for i in v)]
        if len(list_values) == 1:
            return list_values[0]

        for key, value in data.items():
            result = find_list_for_dataframe(value)
            if result is not None:
                return result
    return None

def load_data(file_path):
    """
    Loads data from a file, supporting JSON, YAML, and XML formats.
    Returns the full raw data and a pandas DataFrame of the first suitable list.
    """
    raw_data = None
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path, 'r') as f:
            raw_data = yaml.safe_load(f)
    elif file_path.endswith('.xml'):
        # For XML, we'll try to read it directly with pandas, which is often better for tabular data
        try:
            df = pd.read_xml(file_path)
            # To maintain consistency, we'll convert the df back to a dict for the tree view
            raw_data = df.to_dict(orient='records')
            return raw_data, df
        except Exception:
             tree = etree.parse(file_path)
             raw_data = etree_to_dict(tree.getroot())
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    list_for_df = find_list_for_dataframe(raw_data)
    df = pd.DataFrame(list_for_df) if list_for_df else pd.DataFrame()
    return raw_data, df

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