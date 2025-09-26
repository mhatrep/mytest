import pandas as pd
import tempfile
import os

# Each function should accept a DataFrame and return a string of HTML content.
# They may raise exceptions which should be caught by the main application.

def run_ydata_profiling(df: pd.DataFrame) -> str:
    """Generates a report using ydata-profiling."""
    from ydata_profiling import ProfileReport

    profile = ProfileReport(df, title="YData-Profiling Report")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8') as tmp_file:
        profile.to_file(tmp_file.name)
        filepath = tmp_file.name

    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    os.unlink(filepath)
    return html_content

def run_csvkit(file_path: str, delimiter: str) -> dict:
    """Generates a raw stats report using csvkit in multiple formats."""
    import subprocess

    reports = {}

    # TXT format (default)
    cmd_txt = ["csvstat", "--delimiter", delimiter, file_path]
    result_txt = subprocess.run(cmd_txt, capture_output=True, text=True, check=True, encoding='utf-8')
    reports['txt'] = result_txt.stdout

    # JSON format
    cmd_json = ["csvstat", "--delimiter", delimiter, "--json", file_path]
    result_json = subprocess.run(cmd_json, capture_output=True, text=True, check=True, encoding='utf-8')
    reports['json'] = result_json.stdout

    # CSV format
    cmd_csv = ["csvstat", "--delimiter", delimiter, "--csv", file_path]
    result_csv = subprocess.run(cmd_csv, capture_output=True, text=True, check=True, encoding='utf-8')
    reports['csv'] = result_csv.stdout

    return reports

def run_sweetviz(df: pd.DataFrame) -> str:
    """Generates a report using Sweetviz."""
    import sweetviz as sv

    report = sv.analyze(df)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8') as tmp_file:
        report.show_html(filepath=tmp_file.name, open_browser=False)
        filepath = tmp_file.name

    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    os.unlink(filepath)
    return html_content
