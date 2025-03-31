import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def decrypt_private_key(encrypted_data, pin):
    # Extract salt, iv and encrypted private key from encrypted_data
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    encrypted_key = encrypted_data[32:]

    # Hash the private key analogically to previous encryption, use the same salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    aes_key = kdf.derive(pin.encode('utf-8'))

    # Creating cipher using aes_key (hashed pin) and iv
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()

    # Decryption of encrypted private key
    padded_data = decryptor.update(encrypted_key) + decryptor.finalize()

    # Deleting padding from decrypted private key
    padding_length = padded_data[-1]
    private_key_pem = padded_data[:-padding_length]

    # Return decrypted private key in PEM format
    try:
        load_pem_private_key(private_key_pem, password=None)
        return private_key_pem
    except Exception:
        raise ValueError("Invalid PIN. Unable to read the key.")


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

        # Converting 4096-bit private key to PEM format
        private_key_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Creating 16 bytes long random salt
        salt = os.urandom(16)

        # Creating AES key from users PIN and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        aes_key = kdf.derive(pin.encode('utf-8'))

        # Creating random initialization vector so we get different ciphertext for same files
        iv = os.urandom(16)

        # Creating cipher using aes_key (hashed pin) and iv
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        # Padding privet key bytes so padded_data is multiplicity of 16
        padded_data = private_key_bytes + bytes([16 - len(private_key_bytes) % 16] * (16 - len(private_key_bytes) % 16))

        # Encrypting key with encryptor object
        encrypted_key = encryptor.update(padded_data) + encryptor.finalize()

        # Result of our encryption is 16 bytes of salt, 16 bytes of iv and our encrypted private key
        result = salt + iv + encrypted_key
        return result

