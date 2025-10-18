import json
import yaml
import xml.etree.ElementTree as ET
from PyQt6.QtCore import QFileInfo

def load_data(file_path):
    """
    Loads data from a file and returns the parsed data.
    The file format is determined by the file extension.
    """
    file_info = QFileInfo(file_path)
    extension = file_info.suffix().lower()

    with open(file_path, "r") as f:
        if extension == "json":
            return json.load(f)
        elif extension in ["yaml", "yml"]:
            return yaml.safe_load(f)
        elif extension == "xml":
            tree = ET.parse(f)
            return _xml_to_dict(tree.getroot())
        else:
            raise ValueError(f"Unsupported file format: {extension}")

def _xml_to_dict(root):
    """
    Converts an XML element to a dictionary.
    """
    def _parse_element(element):
        data = {}
        if element.attrib:
            data["@attributes"] = element.attrib
        if element.text and element.text.strip():
            data["#text"] = element.text.strip()

        children = list(element)
        if children:
            for child in children:
                child_data = _parse_element(child)
                if child.tag in data:
                    if not isinstance(data[child.tag], list):
                        data[child.tag] = [data[child.tag]]
                    data[child.tag].append(child_data)
                else:
                    data[child.tag] = child_data
        return data

    return {root.tag: _parse_element(root)}