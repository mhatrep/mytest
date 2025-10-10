import sys
import csv
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QListWidget, QLabel

def transpose_csv_files(file_paths, output_dir='vertical'):
    """
    Transposes a list of CSV files and saves them to the output directory.
    Returns the number of files successfully transposed.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    count = 0
    for file_path in file_paths:
        with open(file_path, 'r', newline='') as infile:
            reader = csv.reader(infile)
            all_rows = list(reader)

        if not all_rows:
            continue

        transposed_data = list(map(list, zip(*all_rows)))

        # Generate the new header
        num_data_cols = len(all_rows)
        new_header = ['COLUMN_NAME'] + [f'DATA_{i:02d}' for i in range(1, num_data_cols)]


        base_name = os.path.basename(file_path)
        new_file_name = os.path.splitext(base_name)[0] + '_vertical.csv'
        new_file_path = os.path.join(output_dir, new_file_name)

        with open(new_file_path, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(new_header)
            writer.writerows(transposed_data)
        count += 1
    return count

class CSVPivot(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('CSV Transposer')
        self.layout = QVBoxLayout()

        self.select_button = QPushButton('Select CSV Files')
        self.select_button.clicked.connect(self.select_files)
        self.layout.addWidget(self.select_button)

        self.file_list = QListWidget()
        self.layout.addWidget(self.file_list)

        self.transpose_button = QPushButton('Transpose and Save')
        self.transpose_button.clicked.connect(self.transpose_and_update_status)
        self.layout.addWidget(self.transpose_button)

        self.status_label = QLabel('')
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)

    def select_files(self):
        self.file_list.clear()
        files, _ = QFileDialog.getOpenFileNames(self, "Select CSV Files", "", "CSV Files (*.csv)")
        if files:
            for file in files:
                self.file_list.addItem(file)

    def transpose_and_update_status(self):
        files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        if not files:
            self.status_label.setText('No files selected.')
            return

        try:
            transposed_count = transpose_csv_files(files)
            self.status_label.setText(f'{transposed_count} files transposed successfully!')
        except Exception as e:
            self.status_label.setText(f'An error occurred: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CSVPivot()
    ex.show()
    sys.exit(app.exec())
