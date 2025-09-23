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

1.  **Open a CSV file:**
    *   Click on the "Open" button in the toolbar or go to "File -> Open".
    *   Select a CSV file from your local machine. The application assumes the file is comma-delimited.

2.  **Filter data:**
    *   Type in the search bar at the top to filter the data in the table. The filtering is case-insensitive and applies to all columns.

3.  **Profile data (using csvstat):**
    *   Click on the "Profile Data (csvstat)" button or go to "Tools -> Profile Data (csvstat)".
    *   You will be prompted to select an output format (`.txt`, `.json`, or `.csv`).
    *   This generates a raw statistical report using `csvkit csvstat`.
    *   The report is saved to a temporary file and opened automatically.

4.  **Generate Modeling Report:**
    *   Click on the "Generate Modeling Report" button or go to "Tools -> Generate Modeling Report".
    *   This analyzes the data and provides data modeling recommendations in a new dialog window.
    *   The recommendations are based on uniqueness, nulls, cardinality, and other statistical properties.

### Sample Data

A sample CSV file named `sample_data.csv` is included in the root of the project. You can use this file to test the application.
