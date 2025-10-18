# Data Viewer

A lightweight Python/Qt6 data viewer for JSON, YAML, and XML files.

## Running the Application

To run the application, make sure you have the required dependencies installed, then run the `main` module from the root directory of the project:

```bash
pip install -r requirements.txt
python -m src.main
```

## Known Limitations

This is a work in progress. The following features are not yet implemented:

*   **Large File Handling:** The application currently loads the entire file into memory, which may cause issues with very large files.
*   **"Nested Explode" Toggle:** There is no option to switch between the flattened view and a hierarchical table view.
*   **Live Expand/Collapse in Table:** The table view does not have expand/collapse controls.