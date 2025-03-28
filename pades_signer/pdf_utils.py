import fitz
import hashlib

def compute_document_hash(pdf_path):
    pdf_document = fitz.open(pdf_path)
    content = b""
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        content += page.get_text("text").encode('utf-8')
    
    hash_obj = hashlib.sha256(content)
    pdf_document.close()
    return hash_obj.digest()
