## CSV Profiler

This is a Python/Qt6 application for profiling CSV data.

### How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the application:**
    ```bash
    python3 src/main.py
    ```

### How to Use

1.  **Open one or more CSV files:**
    *   Click on the "Open" button in the toolbar or go to "File -> Open".
    *   You can select multiple CSV files from your local machine.
    *   Each file will be opened in a new tab. The application assumes files are comma-delimited and UTF-8 encoded.

2.  **Filter data:**
    *   Type in the search bar at the top to filter the data in the currently active tab.

3.  **Generate a Report:**
    *   Click on the "Generate Report" button or go to "Tools -> Generate Report".
    *   A dialog will appear. Choose the type of profiler you want to use from the dropdown menu.
    *   Click "Generate".
    *   A "Save As..." dialog will appear. Choose a location and filename for your report.
    *   **Note:** If you select "csvkit (raw stats)", the application will save three files (`.txt`, `.json`, and `.csv`) using the name you provide as a base. For all other profilers, it will save a single file.
    *   You can choose to have the file(s) opened automatically after saving.

### Sample Data

A sample CSV file named `sample_data.csv` is included in the root of the project. You can use this file to test the application.
