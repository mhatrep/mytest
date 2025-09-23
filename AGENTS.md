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
    *   Select a CSV file from your local machine. The application assumes the file is comma-delimited and UTF-8 encoded.

2.  **Filter data:**
    *   Type in the search bar at the top to filter the data in the table. The filtering is case-insensitive and applies to all columns.

3.  **Generate a Report:**
    *   Click on the "Generate Report" button or go to "Tools -> Generate Report".
    *   A dialog will appear. Choose the type of profiler you want to use from the dropdown menu.
    *   Click "Generate".
    *   A "Save As..." dialog will appear. Choose a location and filename for your report.
    *   You can choose to have the file opened automatically after it is saved.

### Sample Data

A sample CSV file named `sample_data.csv` is included in the root of the project. You can use this file to test the application.
