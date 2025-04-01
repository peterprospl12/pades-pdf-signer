"""
Main entry point for the PAdES Signer application.

This module initializes and runs the main application window of the PAdES Signer,
a tool for creating and verifying digital signatures in PDF documents.

The application provides functionality for:
- Generating asymmetric key pairs (public and private keys)
- Encrypting and storing private keys on USB drives
- Signing PDF documents with cryptographic signatures
- Verifying the authenticity of signed PDF documents

Usage:
    Simply run this script without arguments to start the application:
    $ python run_pades_signer.py
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
