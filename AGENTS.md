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
    *   Select a CSV file from your local machine.
    *   Enter the delimiter for your CSV file in the dialog that pops up.

2.  **Filter data:**
    *   Type in the search bar at the top to filter the data in the table. The filtering is case-insensitive and applies to all columns.

3.  **Profile data:**
    *   Click on the "Profile Data" button in the toolbar or go to "File -> Profile Data".
    *   You will be prompted to select an output format (`.txt` or `.json`).
    *   This will generate a report using `csvkit csvstat`.
    *   The report will be saved to a temporary file and opened automatically.

### Sample Data

A sample CSV file named `sample_data.csv` is included in the root of the project. You can use this file to test the application.
