import pymupdf
import argparse

def create_dummy_pdf(filename="test.pdf", num_pages=5):
    doc = pymupdf.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 72), f"This is page {i+1}.")
    doc.save(filename)
    doc.close()
    print(f"Dummy PDF file '{filename}' with {num_pages} pages created successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a dummy PDF file.")
    parser.add_argument("--filename", default="test.pdf", help="The name of the output PDF file.")
    parser.add_argument("--num_pages", type=int, default=5, help="The number of pages in the PDF.")
    args = parser.parse_args()

    create_dummy_pdf(filename=args.filename, num_pages=args.num_pages)