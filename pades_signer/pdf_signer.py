import os
import time
import fitz  
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import json
from .pdf_utils import compute_document_hash

class PDFSigner:
    
    def __init__(self, private_key=None):
        self.private_key = private_key
        
    def set_private_key(self, private_key):
        self.private_key = private_key
        
    def sign_document(self, pdf_path, output_path, signer_info=None):
        if not self.private_key:
            raise ValueError("No private key available for signing")
            
        document_hash = compute_document_hash(pdf_path)
        
        signature = self.private_key.sign(
            document_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        if signer_info is None:
            signer_info = {}
            
        signature_data = {
            "version": "1.0",
            "timestamp": time.time(),
            "signer": signer_info,
            "signature": base64.b64encode(signature).decode('utf-8'),
            "hash_algorithm": "SHA-256"
        }
        
        pdf_document = fitz.open(pdf_path)
        
        metadata = pdf_document.metadata
        metadata["pades_signature"] = json.dumps(signature_data)
        pdf_document.set_metadata(metadata)
        
        last_page = pdf_document[-1]
        
        signature_text = f"Digitally signed by: {signer_info.get('name', 'Unknown')}\n"
        signature_text += f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        page_rect = last_page.rect
        signature_rect = fitz.Rect(
            page_rect.width - 200, 
            page_rect.height - 100, 
            page_rect.width - 20, 
            page_rect.height - 20
        )
        
        last_page.draw_rect(signature_rect, color=(0, 0, 0))
        last_page.insert_textbox(
            signature_rect, 
            signature_text, 
            fontsize=9, 
            align=1
        )
        
        pdf_document.save(output_path)
        pdf_document.close()
        
        return output_path
