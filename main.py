import os
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

PENDINGS_DIR = Path(os.getenv("PENDINGS_DIR", "/vault/pendings"))

app = FastAPI(
    title="Toxicology Vault — PDF Uploader",
    description="上傳 PDF 到 toxicology-vault/pendings/ 供 MinerU pipeline 處理",
    version="1.0.0",
)


@app.on_event("startup")
async def startup():
    PENDINGS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=_html_page(), status_code=200)


@app.post("/upload", summary="上傳 PDF 到 pendings/")
async def upload_pdf(files: Annotated[list[UploadFile], File(description="一或多個 PDF 檔案")]):
    results = []
    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            results.append({"filename": file.filename, "status": "error", "detail": "非 PDF 檔案，已略過"})
            continue

        dest = PENDINGS_DIR / file.filename
        # 若已存在，加後綴避免覆蓋
        if dest.exists():
            stem = Path(file.filename).stem
            suffix = Path(file.filename).suffix
            counter = 1
            while dest.exists():
                dest = PENDINGS_DIR / f"{stem}_{counter}{suffix}"
                counter += 1

        try:
            with dest.open("wb") as f:
                shutil.copyfileobj(file.file, f)
            results.append({"filename": dest.name, "status": "ok", "path": str(dest)})
        except Exception as e:
            results.append({"filename": file.filename, "status": "error", "detail": str(e)})
        finally:
            await file.close()

    return JSONResponse(content={"results": results})


@app.get("/pendings", summary="列出 pendings/ 中的 PDF")
async def list_pendings():
    if not PENDINGS_DIR.exists():
        return {"files": []}
    pdfs = sorted(p.name for p in PENDINGS_DIR.iterdir() if p.suffix.lower() == ".pdf")
    return {"count": len(pdfs), "files": pdfs}


@app.get("/health")
async def health():
    return {"status": "ok", "pendings_dir": str(PENDINGS_DIR), "exists": PENDINGS_DIR.exists()}


def _html_page() -> str:
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Toxicology Vault — PDF Uploader</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      margin: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 48px 16px;
    }
    .card {
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 40px;
      width: 100%;
      max-width: 560px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    }
    h1 { font-size: 1.5rem; margin: 0 0 4px; color: #f8fafc; }
    .subtitle { color: #94a3b8; font-size: 0.875rem; margin: 0 0 32px; }
    .drop-zone {
      border: 2px dashed #475569;
      border-radius: 12px;
      padding: 40px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
      position: relative;
    }
    .drop-zone:hover, .drop-zone.drag-over {
      border-color: #6366f1;
      background: rgba(99,102,241,0.05);
    }
    .drop-zone input[type=file] {
      position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%;
    }
    .drop-zone .icon { font-size: 2.5rem; margin-bottom: 8px; }
    .drop-zone p { color: #94a3b8; margin: 4px 0; font-size: 0.875rem; }
    .drop-zone strong { color: #c7d2fe; }
    .btn {
      display: block; width: 100%; margin-top: 20px;
      padding: 12px; border: none; border-radius: 8px;
      background: #6366f1; color: #fff; font-size: 1rem;
      font-weight: 600; cursor: pointer; transition: background 0.2s;
    }
    .btn:hover:not(:disabled) { background: #4f46e5; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    #results { margin-top: 24px; }
    .result-item {
      padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
      font-size: 0.875rem; display: flex; align-items: center; gap: 10px;
    }
    .result-item.ok { background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); }
    .result-item.error { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); }
    .result-item .status-icon { font-size: 1.1rem; }
    .file-name { font-weight: 600; color: #e2e8f0; }
    .detail { color: #94a3b8; font-size: 0.8rem; }
    .pendings-link {
      display: inline-block; margin-top: 20px; color: #818cf8; font-size: 0.875rem; text-decoration: none;
    }
    .pendings-link:hover { text-decoration: underline; }
    #file-count { color: #c7d2fe; font-size: 0.875rem; margin-top: 8px; min-height: 1.2em; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🧪 Toxicology Vault</h1>
    <p class="subtitle">上傳 PDF → 自動進入 <code>pendings/</code> 等待 MinerU pipeline 處理</p>

    <form id="uploadForm">
      <div class="drop-zone" id="dropZone">
        <input type="file" id="fileInput" name="files" accept=".pdf" multiple>
        <div class="icon">📄</div>
        <p><strong>點擊選擇</strong>或拖曳 PDF 到此處</p>
        <p>支援多檔同時上傳</p>
      </div>
      <div id="file-count"></div>
      <button type="submit" class="btn" id="uploadBtn" disabled>上傳到 pendings/</button>
    </form>

    <div id="results"></div>
    <a href="/pendings" class="pendings-link" target="_blank">📂 查看 pendings/ 現有檔案 →</a>
  </div>

  <script>
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const uploadBtn = document.getElementById('uploadBtn');
    const resultsDiv = document.getElementById('results');
    const fileCountDiv = document.getElementById('file-count');

    function updateFileCount() {
      const n = fileInput.files.length;
      fileCountDiv.textContent = n > 0 ? `已選擇 ${n} 個檔案` : '';
      uploadBtn.disabled = n === 0;
    }

    fileInput.addEventListener('change', updateFileCount);

    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', e => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const dt = new DataTransfer();
      [...e.dataTransfer.files].forEach(f => { if (f.name.toLowerCase().endsWith('.pdf')) dt.items.add(f); });
      fileInput.files = dt.files;
      updateFileCount();
    });

    document.getElementById('uploadForm').addEventListener('submit', async e => {
      e.preventDefault();
      const formData = new FormData();
      [...fileInput.files].forEach(f => formData.append('files', f));
      uploadBtn.disabled = true;
      uploadBtn.textContent = '上傳中…';
      resultsDiv.innerHTML = '';
      try {
        const resp = await fetch('/upload', { method: 'POST', body: formData });
        const data = await resp.json();
        resultsDiv.innerHTML = data.results.map(r => `
          <div class="result-item ${r.status}">
            <span class="status-icon">${r.status === 'ok' ? '✅' : '❌'}</span>
            <div>
              <div class="file-name">${r.filename || '(unknown)'}</div>
              <div class="detail">${r.status === 'ok' ? r.path : r.detail}</div>
            </div>
          </div>`).join('');
      } catch(err) {
        resultsDiv.innerHTML = `<div class="result-item error"><span class="status-icon">❌</span><div><div class="file-name">網路錯誤</div><div class="detail">${err}</div></div></div>`;
      } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '上傳到 pendings/';
        fileInput.value = '';
        updateFileCount();
      }
    });
  </script>
</body>
</html>"""
