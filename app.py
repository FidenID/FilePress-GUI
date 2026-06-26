import os
import zipfile
import uuid
import subprocess
import shutil
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    send_from_directory, flash, jsonify
)
from PIL import Image
import PyPDF2

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / 'uploads'
COMPRESSED_DIR = BASE_DIR / 'compressed'
UPLOAD_DIR.mkdir(exist_ok=True)
COMPRESSED_DIR.mkdir(exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'tif',
    'pdf',
    'zip', 'gz', 'bz2', 'txt', 'doc', 'docx', 'xls', 'xlsx',
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(input_path, output_path, quality, target_format=None):
    img = Image.open(input_path)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGBA')
    else:
        img = img.convert('RGB')

    if target_format and target_format.lower() == 'webp':
        img.save(output_path, 'WEBP', quality=quality)
    elif target_format and target_format.lower() in ('png',):
        img.save(output_path, 'PNG', optimize=True)
    else:
        save_format = img.format or 'JPEG'
        if save_format.upper() == 'PNG':
            img.save(output_path, 'PNG', optimize=True)
        elif save_format.upper() == 'WEBP':
            img.save(output_path, 'WEBP', quality=quality)
        else:
            img.save(output_path, 'JPEG', quality=quality, optimize=True)


def compress_pdf(input_path, output_path):
    reader = PyPDF2.PdfReader(input_path)
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)


def convert_pdf_to_docx(input_path, output_path):
    subprocess.run([
        'libreoffice', '--headless',
        '--infilter=writer_pdf_import',
        '--convert-to', 'docx',
        '--outdir', str(output_path.parent),
        str(input_path)
    ], check=True, capture_output=True, timeout=120)
    out_name = Path(input_path).stem + '.docx'
    result = output_path.parent / out_name
    if result.exists():
        shutil.move(str(result), str(output_path))


def compress_zip(input_path, output_path, level):
    base = os.path.splitext(os.path.basename(input_path))[0]
    zip_path = output_path / f'{base}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=level) as zf:
        zf.write(input_path, arcname=os.path.basename(input_path))
    return zip_path


def get_file_size(path):
    return os.path.getsize(path)


def format_size(size_bytes):
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 ** 2:
        return f'{size_bytes / 1024:.1f} KB'
    elif size_bytes < 1024 ** 3:
        return f'{size_bytes / (1024 ** 2):.1f} MB'
    return f'{size_bytes / (1024 ** 3):.2f} GB'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash(f'File type not supported. Supported: {", ".join(sorted(ALLOWED_EXTENSIONS))}', 'error')
        return redirect(url_for('index'))

    quality = int(request.form.get('quality', 80))
    output_format = request.form.get('output_format', '')
    compress_level = int(request.form.get('compress_level', 6))

    uid = uuid.uuid4().hex
    ext = file.filename.rsplit('.', 1)[1].lower()
    input_filename = f'{uid}_input.{ext}'
    input_path = UPLOAD_DIR / input_filename
    file.save(input_path)

    output_filename = f'{uid}_compressed.{ext}'
    output_path = COMPRESSED_DIR / output_filename

    try:
        if ext in ('pdf',) and output_format == 'DOCX':
            output_filename = f'{uid}_converted.docx'
            output_path = COMPRESSED_DIR / output_filename
            convert_pdf_to_docx(input_path, output_path)
            action = 'converted'
        elif ext in ('pdf',):
            compress_pdf(input_path, output_path)
            action = 'compressed'
        elif ext in ('png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'tif'):
            fmt = output_format if output_format else None
            compress_image(input_path, output_path, quality, fmt)
            action = 'compressed'
            if output_format:
                out_ext = output_format.lower()
                if out_ext == 'jpeg':
                    out_ext = 'jpg'
                output_filename = f'{uid}_compressed.{out_ext}'
                output_path = COMPRESSED_DIR / output_filename
                compress_image(input_path, output_path, quality, output_format)
        elif ext in ('txt', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'gz', 'bz2'):
            zip_result = compress_zip(input_path, output_path.parent, compress_level)
            output_path = zip_result
            output_filename = output_path.name
            action = 'compressed'
        else:
            zip_result = compress_zip(input_path, output_path.parent, compress_level)
            output_path = zip_result
            output_filename = output_path.name
            action = 'compressed'
    except Exception as e:
        flash(f'Compression failed: {str(e)}', 'error')
        return redirect(url_for('index'))

    orig_size = get_file_size(input_path)
    comp_size = get_file_size(output_path)
    ratio = ((orig_size - comp_size) / orig_size) * 100 if orig_size > 0 else 0

    return render_template('result.html',
                           original=file.filename,
                           compressed=output_filename,
                           orig_size=format_size(orig_size),
                           comp_size=format_size(comp_size),
                           ratio=f'{ratio:.1f}',
                           uid=uid,
                           action=action)


@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(COMPRESSED_DIR, filename, as_attachment=True)


@app.route('/preview/<filename>')
def preview(filename):
    return send_from_directory(COMPRESSED_DIR, filename)


@app.errorhandler(413)
def too_large(e):
    flash('File too large (max 50 MB)', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
