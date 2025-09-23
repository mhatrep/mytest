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

def run_dataprep(df: pd.DataFrame) -> str:
    """Generates a report using Dataprep.EDA."""
    from dataprep.eda import create_report

    report = create_report(df)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8') as tmp_file:
        report.save(filename=tmp_file.name)
        filepath = tmp_file.name

    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    os.unlink(filepath)
    return html_content
