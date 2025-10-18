import json
import yaml
from lxml import etree

def load_data(file_path):
    """
    Loads data from a file, supporting JSON, YAML, and XML formats.
    """
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            return json.load(f)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    elif file_path.endswith('.xml'):
        tree = etree.parse(file_path)
        return etree_to_dict(tree.getroot())
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

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