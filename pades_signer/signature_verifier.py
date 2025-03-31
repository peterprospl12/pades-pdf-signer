import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.exceptions import InvalidSignature
from PyPDF2 import PdfReader, PdfWriter
import io


def extract_signature_data(pdf_path):
    reader = PdfReader(pdf_path)
    metadata = reader.metadata

    if not metadata:
        return None

    signature_data = {}
    if '/Signature' in metadata:
        signature_data['signature'] = metadata['/Signature']
    if '/SignedBy' in metadata:
        signature_data['signed_by'] = metadata['/SignedBy']
    if '/SigningDate' in metadata:
        signature_data['signing_date'] = metadata['/SigningDate']

    if not signature_data.get('signature'):
        return None

    return signature_data


class SignatureVerifier:

    def __init__(self, public_key=None):
        self.public_key = public_key

    def verify_signature(self, pdf_path):
        if not self.public_key:
            return False, "No public key provided"

        signature_data = extract_signature_data(pdf_path)
        if not signature_data:
            return False, "No signature provided"

        try:
            # Decode signature
            signature_hex = signature_data.get('signature')
            signature = bytes.fromhex(signature_hex)
        except Exception as e:
            return False, f"Invalid signing format: {str(e)}"

        # Temporary file without signature metadata
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Copy content without metadata
        for page in reader.pages:
            writer.add_page(page)

        # Deleting metadata
        temp_metadata = reader.metadata.copy()
        if '/Signature' in temp_metadata:
            del temp_metadata['/Signature']
        if '/SignedBy' in temp_metadata:
            del temp_metadata['/SignedBy']
        if '/SigningDate' in temp_metadata:
            del temp_metadata['/SigningDate']

        writer.add_metadata(temp_metadata)

        # Save file to memory
        temp_stream = io.BytesIO()
        writer.write(temp_stream)
        temp_stream.seek(0)

        # Compute sha-256 hash without metadata
        hasher = hashlib.sha256()
        hasher.update(temp_stream.getvalue())
        doc_hash = hasher.digest()

        try:
            self.public_key.verify(
                signature,
                doc_hash,
                padding.PKCS1v15(),
                SHA256()
            )
            return True, f"Signature valid! Signed by: {signature_data.get('signed_by')} date: {signature_data.get('signing_date')}"
        except InvalidSignature:
            return False, "Signature verification failed!"
        except Exception as e:
            return False, f"Error during signature verification: {str(e)}"