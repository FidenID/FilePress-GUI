(function () {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const filePreview = document.getElementById('file-preview');
  const fileName = document.getElementById('file-name');
  const fileSize = document.getElementById('file-size');
  const fileIcon = document.getElementById('file-icon');
  const fileRemove = document.getElementById('file-remove');
  const qualitySlider = document.getElementById('quality');
  const qualityValue = document.getElementById('quality-value');
  const form = document.getElementById('compress-form');
  const btn = document.getElementById('compress-btn');
  const btnText = btn.querySelector('.btn-text');
  const spinner = btn.querySelector('.spinner');

  const FILE_ICONS = {
    image: '🖼',
    pdf: '📄',
    zip: '📦',
    doc: '📝',
    text: '📃',
    other: '📁',
  };

  const FILE_CLASSES = {
    jpg: 'image', jpeg: 'image', png: 'image', webp: 'image',
    bmp: 'image', tiff: 'image', tif: 'image',
    pdf: 'pdf',
    zip: 'zip', gz: 'zip', bz2: 'zip', '7z': 'zip', rar: 'zip',
    doc: 'doc', docx: 'doc', xls: 'doc', xlsx: 'doc',
    txt: 'text',
  };

  if (qualitySlider && qualityValue) {
    const updateRange = () => {
      qualityValue.textContent = qualitySlider.value;
      const pct = ((qualitySlider.value - qualitySlider.min) / (qualitySlider.max - qualitySlider.min)) * 100;
      qualitySlider.style.background = `linear-gradient(to right, rgba(0,212,255,0.6) ${pct}%, rgba(255,255,255,0.08) ${pct}%)`;
    };
    qualitySlider.addEventListener('input', updateRange);
    updateRange();
  }

  function getFileType(ext) {
    return FILE_CLASSES[ext] || 'other';
  }

  function getFileIcon(type) {
    return FILE_ICONS[type] || FILE_ICONS.other;
  }

  function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const val = (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0);
    return val + ' ' + units[i];
  }

  function showFileInfo(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    const type = getFileType(ext);
    const icon = getFileIcon(type);

    if (filePreview) {
      fileIcon.className = 'file-icon ' + type;
      fileIcon.textContent = icon;
      fileName.textContent = file.name;
      fileSize.textContent = formatSize(file.size);
      filePreview.classList.add('visible');
    }

    if (dropZone) {
      const content = dropZone.querySelector('.drop-zone-content p');
      if (content) content.textContent = 'File selected — ready to compress';
      dropZone.classList.add('has-file');
    }
  }

  function resetFileInfo() {
    if (filePreview) filePreview.classList.remove('visible');
    if (dropZone) {
      const content = dropZone.querySelector('.drop-zone-content p');
      if (content) content.textContent = 'Drag & drop file here or click to browse';
      dropZone.classList.remove('has-file');
    }
    fileInput.value = '';
  }

  if (fileRemove) {
    fileRemove.addEventListener('click', function (e) {
      e.stopPropagation();
      resetFileInfo();
    });
  }

  if (dropZone && fileInput) {
    dropZone.addEventListener('click', function () {
      if (!filePreview || !filePreview.classList.contains('visible')) {
        fileInput.click();
      }
    });

    fileInput.addEventListener('change', function () {
      if (this.files.length > 0) showFileInfo(this.files[0]);
    });

    dropZone.addEventListener('dragover', function (e) {
      e.preventDefault();
      this.classList.add('dragover');
    });

    ['dragleave', 'dragend'].forEach(function (ev) {
      dropZone.addEventListener(ev, function (e) {
        e.preventDefault();
        this.classList.remove('dragover');
      });
    });

    dropZone.addEventListener('drop', function (e) {
      e.preventDefault();
      this.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        showFileInfo(e.dataTransfer.files[0]);
      }
    });
  }

  if (form && btn) {
    form.addEventListener('submit', function () {
      btn.disabled = true;
      btnText.textContent = 'Compressing...';
      btnText.style.display = '';
      spinner.style.display = 'inline-block';
    });
  }
})();
