import hashlib
from datetime import datetime
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.hashes import SHA256
from PyPDF2 import PdfReader, PdfWriter
import io

class PDFSigner:

    def __init__(self, private_key_pem):
        self.private_key = load_pem_private_key(private_key_pem, password=None)

    def sign_document(self, pdf_path, output_path, signer_name):
        if not self.private_key:
            raise ValueError("No private key available for signing")

        # Open PDF file
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Copying input file to output PDF
        for page in reader.pages:
            writer.add_page(page)

        # Temporary saving document without metadata
        temp_stream = io.BytesIO()
        writer.write(temp_stream)
        temp_stream.seek(0)

        # Hashing the document
        hasher = hashlib.sha256()
        hasher.update(temp_stream.getvalue())
        doc_hash = hasher.digest()

        # Signing PDF hash using our private key
        signature = self.private_key.sign(
            doc_hash,
            padding.PKCS1v15(),
            SHA256()
        )

        # Adding sign metadata
        writer.add_metadata({
            '/SignedBy': signer_name,
            '/Signature': signature.hex(),
            '/SigningDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Save signer pdf file
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        return output_path
