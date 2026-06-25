# FilePress

Web-based file compression tool for images, PDFs, and documents.

## Features

- Image compression (JPG, PNG, WebP, BMP, TIFF) with quality control
- PDF compression via content stream optimization
- File compression (ZIP) with configurable level
- Drag & drop upload
- Before/after size comparison
- Format conversion (convert images to JPEG/PNG/WebP)

## Requirements

- Python 3.10+
- Flask
- Pillow
- PyPDF2

## Installation

```bash
git clone <repo-url>
cd filepress
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## License

MIT
