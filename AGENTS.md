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

4.  **Export Unique Values:**
    *   Click on the "Export Unique Values" button or go to "Tools -> Export Unique Values".
    *   A dialog will appear with several options for case sensitivity, frequency counts, and sorting.
    *   You will then be prompted to select an output directory.
    *   The application will create a sub-directory named after your file, and inside it, a separate `.txt` file for each column (prefixed with the column number) containing its unique values.

5.  **Find Data Grain:**
    *   Click on the "Find Data Grain" button or go to "Tools -> Find Data Grain".
    *   This feature analyzes incremental combinations of columns based on their order in the file (`C1`, `C1+C2`, `C1+C2+C3`, etc.) to find the smallest set that uniquely identifies each row.
    *   An options dialog will let you configure normalization options for the analysis.
    *   The results are shown in a new dialog, highlighting any candidate keys found. You can copy the results table to your clipboard from this dialog.

6.  **Find Hierarchies:**
    *   Click on the "Find Hierarchies" button or go to "Tools -> Find Hierarchies".
    *   This feature analyzes all pairs of columns to detect one-to-many relationships, which indicate a hierarchy (e.g., `Parent -> Child`).
    *   The results, including any chained hierarchies found (e.g., `Country -> State -> City`), are displayed in a new report dialog.

### Sample Data

A sample CSV file named `sample_data.csv` is included in the root of the project. You can use this file to test the application.
