import os
import sys
import time
from PyQt5.QtWidgets import (QMainWindow, QAction, QFileDialog, QLabel, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, 
                            QInputDialog, QLineEdit, QDialog, QProgressBar, QTabWidget)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from key_manager.usb_storage import UsbStorage
from pades_signer.pdf_signer import PDFSigner
from pades_signer.signature_verifier import SignatureVerifier
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class USBDetectorThread(QThread):
    usb_detected = pyqtSignal(list)
    
    def run(self):
        while True:
            usb_drives = UsbStorage.get_usb_drives()
            self.usb_detected.emit(usb_drives)
            time.sleep(2) 

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PAdES Signature Application")
        self.setGeometry(100, 100, 800, 600)
        
        self.private_key = None
        self.public_key = None
        self.usb_path = None
        self.encrypted_key_path = None
        
        self.init_ui()
        self.start_usb_detection()
        
    def init_ui(self):
        """Initialize UI components."""
        self.tabs = QTabWidget()
        self.sign_tab = QWidget()
        self.verify_tab = QWidget()
        
        self.tabs.addTab(self.sign_tab, "Sign Document")
        self.tabs.addTab(self.verify_tab, "Verify Signature")
        
        self.setup_sign_tab()
        
        self.setup_verify_tab()
        
        self.setCentralWidget(self.tabs)
        
        self.setup_menu()
        
        self.statusBar = self.statusBar()
        self.usb_status = QLabel("USB Status: Not Connected")
        self.statusBar.addPermanentWidget(self.usb_status)
        
    def setup_sign_tab(self):
        layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.pdf_path_label = QLabel("No PDF selected")
        select_file_button = QPushButton("Select PDF")
        select_file_button.clicked.connect(self.select_pdf_file)
        file_layout.addWidget(self.pdf_path_label)
        file_layout.addWidget(select_file_button)
        
        sign_button = QPushButton("Sign Document")
        sign_button.clicked.connect(self.sign_document)
        
        self.sign_status = QLabel("Ready")
        self.sign_status.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(file_layout)
        layout.addWidget(sign_button)
        layout.addWidget(self.sign_status)
        
        layout.addStretch(1)
        
        self.sign_tab.setLayout(layout)
        
    def setup_verify_tab(self):
        layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.verify_path_label = QLabel("No PDF selected")
        select_file_button = QPushButton("Select Signed PDF")
        select_file_button.clicked.connect(self.select_verify_file)
        file_layout.addWidget(self.verify_path_label)
        file_layout.addWidget(select_file_button)
        
        key_layout = QHBoxLayout()
        self.public_key_label = QLabel("No public key selected")
        select_key_button = QPushButton("Select Public Key")
        select_key_button.clicked.connect(self.select_public_key)
        key_layout.addWidget(self.public_key_label)
        key_layout.addWidget(select_key_button)
        
        verify_button = QPushButton("Verify Signature")
        verify_button.clicked.connect(self.verify_signature)
        
        self.verify_status = QLabel("Ready")
        self.verify_status.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(file_layout)
        layout.addLayout(key_layout)
        layout.addWidget(verify_button)
        layout.addWidget(self.verify_status)
        
        layout.addStretch(1)
        
        self.verify_tab.setLayout(layout)
        
    def setup_menu(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def start_usb_detection(self):
        self.usb_detector_thread = USBDetectorThread()
        self.usb_detector_thread.usb_detected.connect(self.update_usb_status)
        self.usb_detector_thread.start()
        
    def update_usb_status(self, usb_drives):
        if usb_drives:
            self.usb_path = usb_drives[0]
            self.usb_status.setText(f"USB Connected: {self.usb_path}")
            self.check_for_keys()
        else:
            self.usb_path = None
            self.encrypted_key_path = None
            self.usb_status.setText("USB Status: Not Connected")
            
    def check_for_keys(self):
        if not self.usb_path:
            return
            
        for filename in os.listdir(self.usb_path):
            if filename.endswith('.key'):
                self.encrypted_key_path = os.path.join(self.usb_path, filename)
                self.usb_status.setText(f"USB Connected: {self.usb_path} (Key found)")
                return
    
    def select_pdf_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_path_label.setText(file_path)
            
    def select_verify_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Signed PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.verify_path_label.setText(file_path)
            
    def select_public_key(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Public Key", "", "PEM Files (*.pem)")
        if file_path:
            try:
                with open(file_path, "rb") as key_file:
                    self.public_key = serialization.load_pem_public_key(key_file.read())
                self.public_key_label.setText(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load public key: {str(e)}")
    
    def decrypt_private_key(self, encrypted_data, pin):
        salt = encrypted_data[:16]
        iv = encrypted_data[16:32]
        encrypted_key = encrypted_data[32:]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        aes_key = kdf.derive(pin.encode('utf-8'))
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_key) + decryptor.finalize()
        
        padding_length = padded_data[-1]
        private_key_pem = padded_data[:-padding_length]
        
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )
        
        return private_key
            
    def sign_document(self):
        if not self.encrypted_key_path:
            QMessageBox.warning(self, "Error", "No private key found on USB drive")
            return
            
        pdf_path = self.pdf_path_label.text()
        if pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
            QMessageBox.warning(self, "Error", "Please select a valid PDF file")
            return
            
        pin, ok = QInputDialog.getText(self, "PIN Required", "Enter your PIN to decrypt the private key:", QLineEdit.Password)
        if not ok or not pin:
            return
            
        try:
            encrypted_data = UsbStorage.load_from_usb(self.encrypted_key_path)
            
            self.sign_status.setText("Decrypting private key...")
            self.private_key = self.decrypt_private_key(encrypted_data, pin)
            
            signer_name, ok = QInputDialog.getText(self, "Signer Information", "Enter signer name:")
            if not ok:
                signer_name = "Unknown"
                
            file_dir = os.path.dirname(pdf_path)
            file_name = os.path.basename(pdf_path)
            output_path = os.path.join(file_dir, f"signed_{file_name}")
            
            self.sign_status.setText("Signing document...")
            
            pdf_signer = PDFSigner(self.private_key)
            signer_info = {"name": signer_name}
            output_path = pdf_signer.sign_document(pdf_path, output_path, signer_info)
            
            self.sign_status.setText(f"Document signed successfully and saved to: {output_path}")
            QMessageBox.information(self, "Success", f"Document signed successfully and saved to: {output_path}")
            
        except Exception as e:
            self.sign_status.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to sign document: {str(e)}")
            
    def verify_signature(self):
        if not self.public_key:
            QMessageBox.warning(self, "Error", "Please select a public key first")
            return
            
        pdf_path = self.verify_path_label.text()
        if pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
            QMessageBox.warning(self, "Error", "Please select a valid PDF file")
            return
            
        try:
            self.verify_status.setText("Verifying signature...")
            
            verifier = SignatureVerifier(self.public_key)
            is_valid, message = verifier.verify_signature(pdf_path)
            
            if is_valid:
                self.verify_status.setText("Signature is valid")
                QMessageBox.information(self, "Verification Result", "Signature is valid!")
            else:
                self.verify_status.setText(f"Invalid signature: {message}")
                QMessageBox.warning(self, "Verification Result", f"Invalid signature: {message}")
                
        except Exception as e:
            self.verify_status.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to verify signature: {str(e)}")
            
    def show_about(self):
        QMessageBox.about(self, "About PAdES Signer",
            "PAdES Signature Application\n\n"
            "This application allows you to create and verify qualified electronic signatures "
            "according to PAdES standard.\n\n"
            "Private keys are securely stored on USB drives, encrypted with AES-256."
        )