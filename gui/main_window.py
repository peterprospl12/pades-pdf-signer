"""
Module containing the graphical user interface for the PAdES Signer application.
"""

import os
import sys
import time
from PyQt5.QtWidgets import (QMainWindow, QAction, QFileDialog, QLabel, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, 
                            QInputDialog, QLineEdit, QTabWidget, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from key_manager.usb_storage import UsbStorage
from pades_signer.pdf_signer import PDFSigner
from pades_signer.signature_verifier import SignatureVerifier
from cryptography.hazmat.primitives import serialization
from key_manager.key_generator import KeyGenerator, decrypt_private_key

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class USBDetectorThread(QThread):
    """
    Thread for continuous USB drive detection.

    Signals:
        usb_detected (list): Signal emitted when USB drives are detected.
    """
    usb_detected = pyqtSignal(list)
    
    def run(self):
        """
        Thread execution method that continuously checks for USB drives.
        """
        while True:
            usb_drives = UsbStorage.get_usb_drives()
            self.usb_detected.emit(usb_drives)
            time.sleep(2)

class MainWindow(QMainWindow):
    """
    Main application window containing UI elements for signing and verifying documents.
    """
    
    def __init__(self):
        """
        Initialize the main window and UI components.
        """
        super().__init__()

        self.public_key_path = None
        self.public_key_path_label = None
        self.key_status = None
        self.pin_input = None
        self.usb_detector_thread = None
        self.pin_label = None
        self.verify_status = None
        self.public_key_label = None
        self.verify_path_label = None
        self.sign_status = None
        self.pdf_path_label = None
        self.usb_status = None
        self.status_bar = None
        self.key_tab = None
        self.verify_tab = None
        self.sign_tab = None
        self.tabs = None
        self.setWindowTitle("PAdES Signature Application")
        self.setGeometry(100, 100, 800, 200)
        
        self.private_key = None
        self.public_key = None
        self.usb_path = None
        self.encrypted_key_path = None
        
        self.init_ui()
        self.start_usb_detection()
        
    def init_ui(self):
        """
        Initialize UI components.
        """
        self.tabs = QTabWidget()
        self.sign_tab = QWidget()
        self.verify_tab = QWidget()
        self.key_tab = QWidget()
        
        self.tabs.addTab(self.sign_tab, "Sign Document")
        self.tabs.addTab(self.verify_tab, "Verify Signature")
        self.tabs.addTab(self.key_tab, "Generate Key")

        self.setup_sign_tab()
        self.setup_verify_tab()
        self.setup_key_tab()

        self.setCentralWidget(self.tabs)
        
        self.setup_menu()
        
        self.status_bar = self.statusBar()
        self.usb_status = QLabel("USB Status: Not Connected")
        self.status_bar.addPermanentWidget(self.usb_status)
        
    def setup_sign_tab(self):
        """
        Configure the Sign Document tab with necessary UI components.

        Creates a layout with file selection, document signing button and status indicator.
        """
        layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.pdf_path_label = QLabel("No PDF selected")
        select_file_button = QPushButton("Select PDF")
        select_file_button.clicked.connect(self.select_pdf_file)
        file_layout.addWidget(self.pdf_path_label)
        file_layout.addWidget(select_file_button)
        
        sign_button = QPushButton("Sign Document")
        sign_button.clicked.connect(self.sign_document)

        if self.private_key is not None:
            self.sign_status = QLabel("Ready")
        else:
            self.sign_status = QLabel("No private key detected!")

        self.sign_status.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(file_layout)
        layout.addWidget(sign_button)
        layout.addWidget(self.sign_status)
        
        layout.addStretch(1)
        
        self.sign_tab.setLayout(layout)
        
    def setup_verify_tab(self):
        """
        Configure the Verify Signature tab with necessary UI components.

        Creates a layout with signed file selection, public key selection,
        signature verification button and status indicator.
        """
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

    def setup_key_tab(self):
        """
        Configure the Generate Key tab with necessary UI components.

        Creates a layout with PIN entry field, public key save path selection,
        key generation button and status indicator.
        """
        layout = QVBoxLayout()

        pin_layout = QHBoxLayout()
        self.pin_label = QLabel("Enter PIN:")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        pin_layout.addWidget(self.pin_label)
        pin_layout.addWidget(self.pin_input)

        path_layout = QHBoxLayout()
        self.public_key_path_label = QLabel("No public key path selected")
        select_path_button = QPushButton("Select Public Key Save Path")
        select_path_button.clicked.connect(self.select_public_key_path)
        path_layout.addWidget(self.public_key_path_label)
        path_layout.addWidget(select_path_button)

        generate_key_button = QPushButton("Generate and Save Key")
        generate_key_button.clicked.connect(self.generate_and_save_key)

        self.key_status = QLabel("Ready")
        self.key_status.setAlignment(Qt.AlignCenter)

        layout.addLayout(pin_layout)
        layout.addLayout(path_layout)
        layout.addWidget(generate_key_button)
        layout.addWidget(self.key_status)

        layout.addStretch(1)

        self.key_tab.setLayout(layout)

    def select_public_key_path(self):
        """
        Open a folder selection dialog to choose where to save the public key.

        Updates the public_key_path_label with the selected path.
        """
        folder_path = QFileDialog.getExistingDirectory(self, "Pick directory where public key will be saved")
        if folder_path:
            self.public_key_path = folder_path
            self.public_key_path_label.setText(folder_path)
        
    def setup_menu(self):
        """
        Setup the application's menu bar with File and Help menus.
        """
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
        """
        Start the USB detection thread that continuously monitors for connected USB drives.
        """
        self.usb_detector_thread = USBDetectorThread()
        self.usb_detector_thread.usb_detected.connect(self.update_usb_status)
        self.usb_detector_thread.start()
        
    def update_usb_status(self, usb_drives):
        """
        Update the UI with the status of connected USB drives.

        Args:
            usb_drives (list): List of detected USB drive paths.
        """
        if usb_drives:
            self.usb_path = usb_drives[0]
            self.usb_status.setText(f"USB Connected: {self.usb_path}")
            self.check_for_keys()
        else:
            self.usb_path = None
            self.encrypted_key_path = None
            self.usb_status.setText("USB Status: Not Connected")
            self.sign_status.setText("No private key detected!")
            
    def check_for_keys(self):
        """
        Check if any key files exist on the connected USB drive.

        Updates the USB status label with key detection information.
        """
        if not self.usb_path:
            return
            
        for filename in os.listdir(self.usb_path):
            if filename.endswith('.key'):
                self.encrypted_key_path = os.path.join(self.usb_path, filename)
                self.usb_status.setText(f"USB Connected: {self.usb_path} (Key found)")
                self.sign_status.setText("Ready")
                QApplication.processEvents()
                return

        self.sign_status.setText("No private key detected!")
        self.usb_status.setText(f"USB Connected: {self.usb_path} (No key found)")
    
    def select_pdf_file(self):
        """
        Open a file selection dialog to choose a PDF document for signing.

        Updates the pdf_path_label with the selected file path.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_path_label.setText(file_path)
            
    def select_verify_file(self):
        """
        Open a file selection dialog to choose a signed PDF document for verification.

        Updates the verify_path_label with the selected file path.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Signed PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.verify_path_label.setText(file_path)
            
    def select_public_key(self):
        """
        Open a file selection dialog to choose a public key file for signature verification.

        Loads the selected public key and updates the public_key_label with the file path.

        Raises:
            Exception: When the public key cannot be loaded.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Public Key", "", "PEM Files (*.pem)")
        if file_path:
            try:
                with open(file_path, "rb") as key_file:
                    self.public_key = serialization.load_pem_public_key(key_file.read())
                self.public_key_label.setText(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load public key: {str(e)}")


    def sign_document(self):
        """
        Sign a PDF document using the private key stored on the USB drive.

        Prompts for PIN to decrypt the private key, then signs the document
        and saves it with a 'signed_' prefix.

        Updates the sign_status label with progress and result information.
        """
        if not self.encrypted_key_path:
            self.sign_status.setText("No private key found on USB drive")
            QApplication.processEvents()
            return
            
        pdf_path = self.pdf_path_label.text()
        if pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
            self.sign_status.setText("No PDF file selected")
            QApplication.processEvents()
            return
            
        pin, ok = QInputDialog.getText(self, "PIN Required", "Enter your PIN to decrypt the private key:", QLineEdit.Password)
        if not ok or not pin:
            return
            
        try:
            encrypted_data = UsbStorage.load_from_usb(self.encrypted_key_path)
            
            self.sign_status.setText("Decrypting private key...")
            QApplication.processEvents()

            try:
                self.private_key = decrypt_private_key(encrypted_data, pin)
            except ValueError:
                QMessageBox.critical(self, "Invalid PIN", "The PIN you entered is incorrect. Please try again.")
                self.sign_status.setText("Invalid PIN. Operation cancelled.")
                QApplication.processEvents()
                return
            time.sleep(2)
            
            signer_name, ok = QInputDialog.getText(self, "Signer Information", "Enter signer name:")
            if not ok:
                signer_name = "Unknown"
                
            file_dir = os.path.dirname(pdf_path)
            file_name = os.path.basename(pdf_path)
            output_path = os.path.join(file_dir, f"signed_{file_name}")
            
            self.sign_status.setText("Signing document...")
            pdf_signer = PDFSigner(self.private_key)
            output_path = pdf_signer.sign_document(pdf_path, output_path, signer_name)
            QApplication.processEvents()
            time.sleep(2)

            self.sign_status.setText(f"Document signed successfully and saved to: {output_path}")
            QApplication.processEvents()
            time.sleep(2)
            
        except Exception as e:
            self.sign_status.setText(f"Error! Failed to sign document: {str(e)}")
            print(str(e))
            
    def verify_signature(self):
        """
        Verify the digital signature in a PDF document using the selected public key.

        Updates the verify_status label with verification results.
        """
        if not self.public_key:
            self.sign_status.setText("Please select a public key first")
            QApplication.processEvents()
            return
            
        pdf_path = self.verify_path_label.text()
        if pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
            self.sign_status.setText("Please select a valid PDF file")
            QApplication.processEvents()
            return
            
        try:
            self.verify_status.setText("Verifying signature...")
            verifier = SignatureVerifier(self.public_key)
            is_valid, message = verifier.verify_signature(pdf_path)
            QApplication.processEvents()
            time.sleep(2)

            if is_valid:
                self.verify_status.setText("Signature is valid")
                QApplication.processEvents()
            else:
                self.verify_status.setText(f"Invalid signature: {message}")
                QApplication.processEvents()
                
        except Exception as e:
            self.verify_status.setText(f"Error: Failed to verify signature: {str(e)}")
            
    def show_about(self):
        """
        Display an information dialog with details about the application.
        """
        QMessageBox.about(self, "About PAdES Signer",
            "PAdES Signature Application\n\n"
            "This application allows you to create and verify qualified electronic signatures "
            "according to simplified PAdES standard.\n\n"
            "Private keys are securely stored on USB drives, encrypted with AES-256."
        )

    def generate_and_save_key(self):
        """
        Generate a new key pair, encrypt the private key with the provided PIN,
        and save the keys to appropriate locations.

        The private key is encrypted and saved to the USB drive,
        while the public key is saved to the selected path.

        Updates the key_status label with progress and result information.
        """
        pin = self.pin_input.text()
        if not pin:
            self.key_status.setText("Error! Please enter a PIN")
            QApplication.processEvents()
            return

        if not self.usb_path:
            self.key_status.setText("Error! No USB drive detected")
            QApplication.processEvents()
            return

        if not self.public_key_path:
            self.key_status.setText("Error! Specify where to save the private key")
            QApplication.processEvents()
            return

        try:
            self.key_status.setText("Creating private and public keys pair...")
            QApplication.processEvents()
            key_generator = KeyGenerator()
            private_key, public_key = key_generator.generate_key_pair()
            time.sleep(2)

            self.key_status.setText("Encrypting private key...")
            QApplication.processEvents()
            encrypted_key = key_generator.encrypt_private_key(pin)
            time.sleep(2)

            self.key_status.setText("Saving key to USB drive...")
            QApplication.processEvents()
            UsbStorage.save_to_usb(self.usb_path, "private_key.key", encrypted_key)
            public_key_file = os.path.join(self.public_key_path, "public_key.pem")
            with open(public_key_file, "wb") as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

            self.key_status.setText("Key generated and saved successfully")
            QApplication.processEvents()

        except Exception as e:
            self.key_status.setText(f"Error! Failed to generate and save key: {str(e)}")
            QApplication.processEvents()