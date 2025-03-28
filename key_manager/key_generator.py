import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class KeyGenerator:
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        
    def generate_key_pair(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        self.public_key = self.private_key.public_key()
        return self.private_key, self.public_key
        
    def encrypt_private_key(self, pin):
        if not self.private_key:
            raise ValueError("No private key available. Generate key pair first.")
        
        private_key_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        aes_key = kdf.derive(pin.encode('utf-8'))
        
        iv = os.urandom(16)
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        
        padded_data = private_key_bytes + bytes([16 - len(private_key_bytes) % 16] * (16 - len(private_key_bytes) % 16))
        encrypted_key = encryptor.update(padded_data) + encryptor.finalize()
        
        result = salt + iv + encrypted_key
        return result
    
    def save_public_key(self, filename):
        if not self.public_key:
            raise ValueError("No public key available. Generate key pair first.")
            
        with open(filename, "wb") as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
