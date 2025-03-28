import json
import base64
import fitz
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

class SignatureVerifier:
    
    def __init__(self, public_key=None):
        self.public_key = public_key
        
    def set_public_key(self, public_key):
        self.public_key = public_key
        
    def extract_signature_data(self, pdf_path):
        pdf_document = fitz.open(pdf_path)
        metadata = pdf_document.metadata
        pdf_document.close()
        
        if "pades_signature" in metadata:
            try:
                return json.loads(metadata["pades_signature"])
            except json.JSONDecodeError:
                return None
        return None
        
    def compute_document_hash(self, pdf_path):
        pdf_document = fitz.open(pdf_path)
        content = b""
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            content += page.get_text("text").encode('utf-8')
            
        hash_obj = hashlib.sha256(content)
        return hash_obj.digest()
        
    def verify_signature(self, pdf_path):
        if not self.public_key:
            return False, "No public key provided for verification"
        
        signature_data = self.extract_signature_data(pdf_path)
        if not signature_data:
            return False, "No signature found in document"
        
        try:
            signature = base64.b64decode(signature_data["signature"])
        except:
            return False, "Invalid signature format"
        
        document_hash = self.compute_document_hash(pdf_path)
        
        try:
            self.public_key.verify(
                signature,
                document_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True, "Signature is valid"
        except InvalidSignature:
            return False, "Signature verification failed"
        except Exception as e:
            return False, f"Error during verification: {str(e)}"
