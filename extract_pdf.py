import PyPDF2
import sys

def extract_pdf_text(pdf_path):
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"PDF has {num_pages} pages\n")
            print("=" * 80)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                print(f"\n--- Page {page_num + 1} ---\n")
                print(text)
                print("\n" + "=" * 80)
                
    except Exception as e:
        print(f"Error reading PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    pdf_file = r"docs\PI1_Trabajo de Investigación 2025-02-2.pdf"
    extract_pdf_text(pdf_file)
