from PyPDF2 import PdfReader
def extract_text_from_pdf(file_path:str) -> str:
    try:
        with open(file_path,"rb") as file:
            pdf_reader = PdfReader(file)
            text = ""

            for index,page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {index + 1} ---\n"
                text += page_text

            return text
    except Exception as e:
        print(f"Error while processing PDF {e}")