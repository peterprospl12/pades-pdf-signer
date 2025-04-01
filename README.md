# PAdES PDF Signer

A desktop application for creating and verifying qualified electronic signatures in PDF documents according to the PAdES (PDF Advanced Electronic Signature) standard.
![pades_app_image](https://github.com/user-attachments/assets/0a3ba155-239c-45f2-a0ce-73e913718525)

## Features

- **Secure Key Management**: Private keys are stored encrypted on USB drives using AES-256
- **USB Drive Integration**: Automatic detection of USB drives containing cryptographic keys
- **PIN Protection**: Private keys require PIN authentication for use
- **PDF Signing**: Sign PDF documents with cryptographic signatures
- **Signature Verification**: Verify the authenticity of signed documents

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd pades-pdf-signer
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

Start the application with:
```
python run_pades_signer.py
```

## Project Structure

- `gui/`: User interface components
- `key_manager/`: Key generation and USB storage functionality
- `pades_signer/`: PDF signing and verification implementation


## Documentation
Complete project documentation is available in the `docs/` directory or can be generated using Doxygen.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
