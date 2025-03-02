document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('file-input');
  const fileList = document.getElementById('file-list');
  const piiResults = document.getElementById('pii-results');
  let redactedUrl = '';

  
  const modal = document.getElementById('redact-modal');
  const modalImage = document.getElementById('redacted-image');
  const downloadLink = document.getElementById('download-link');
  const closeModal = document.querySelector('.close');

  
  fileInput.addEventListener('change', (event) => {
    const files = event.target.files;
    if (files.length > 0) {
      fileList.innerHTML = ''; 
      for (const file of files) {
        processFile(file);
      }
    }
  });

  const uploadContainer = document.querySelector('.upload-container');
  uploadContainer.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadContainer.classList.add('drag-active');
  });

  uploadContainer.addEventListener('dragleave', () => {
    uploadContainer.classList.remove('drag-active');
  });

  uploadContainer.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadContainer.classList.remove('drag-active');
    const files = e.dataTransfer.files;
    fileInput.files = files;
    fileInput.dispatchEvent(new Event('change'));
  });

  function processFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';

    const fileName = document.createElement('span');
    fileName.className = 'file-name';
    fileName.textContent = truncateFileName(file.name, 20);
    fileItem.appendChild(fileName);

    const unsubmitBtn = document.createElement('button');
    unsubmitBtn.className = 'unsubmit-btn';
    unsubmitBtn.textContent = 'Remove';
    unsubmitBtn.addEventListener('click', () => {
      fileItem.remove();
    });
    fileItem.appendChild(unsubmitBtn);

    fileList.appendChild(fileItem);

    fetch('http://localhost:5000/api/upload', {
      method: 'POST',
      body: formData,
    })
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        redactedUrl = data.redacted_url;
        displayPiiResults(data.pii);
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Error processing file: ' + error.message);
      });
  }

  function displayPiiResults(piiList) {
    piiResults.innerHTML = '';

    if (!piiList || piiList.length === 0) {
      piiResults.innerHTML = '<div class="no-pii">No sensitive PII detected</div>';
      return;
    }

    const header = document.createElement('h2');
    header.textContent = 'PII Detected in Document';
    piiResults.appendChild(header);

    const table = document.createElement('table');
    table.className = 'pii-table';

    const headerRow = table.insertRow();
    ['Type', 'Value', 'Risk'].forEach(text => {
      const th = document.createElement('th');
      th.textContent = text;
      headerRow.appendChild(th);
    });

    piiList.forEach(pii => {
      const row = table.insertRow();
      row.insertCell().textContent = pii.type;
      row.insertCell().textContent = pii.value;
      const riskCell = row.insertCell();
      riskCell.textContent = pii.risk;

      riskCell.classList.add('risk-' + pii.risk.toLowerCase());
    });

    piiResults.appendChild(table);

    const redactBtn = document.createElement('button');
    redactBtn.className = 'btn-primary';
    redactBtn.textContent = 'Redact Document';
    redactBtn.addEventListener('click', () => {
      openModal();
    });
    piiResults.appendChild(redactBtn);
  }

  function openModal() {
    modal.style.display = 'block';
    modalImage.src = redactedUrl;
    downloadLink.href = redactedUrl;
  }

  
  closeModal.addEventListener('click', () => {
    modal.style.display = 'none';
  });

  window.addEventListener('click', (event) => {
    if (event.target == modal) {
      modal.style.display = 'none';
    }
  });

  function truncateFileName(name, maxLength) {
    return name.length > maxLength ? name.substring(0, maxLength) + '...' : name;
  }
});
