def process_documents(file_path: str,document_id:str):
    print(f"Processing Document {file_path} with {document_id}")
    try:
        return True
    except Exception as e:
        print(f"Error in proeccession file {file_path}")
        return False
    