from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from uuid import uuid4
import shutil
import os

from ocr_service import process_pdf, process_word
from job_store import job_store
from field_extractor import extract_fields

app = FastAPI(title="OCR Server")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/ocr/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    PDF 또는 Word 파일 업로드 → 비동기 OCR 처리 시작
    """
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail="PDF 또는 Word 파일만 지원합니다.")

    job_id = str(uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")

    # 파일 저장
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 작업 초기화
    job_store[job_id] = {"status": "pending", "result": None, "error": None}

    # 백그라운드 처리 등록
    if ext == ".pdf":
        background_tasks.add_task(process_pdf, job_id, save_path)
    else:
        background_tasks.add_task(process_word, job_id, save_path)

    return {"job_id": job_id, "status": "pending"}


@app.get("/ocr/status/{job_id}")
async def get_status(job_id: str):
    """
    작업 상태 조회 (pending / processing / done / error)
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="존재하지 않는 job_id입니다.")
    return job


@app.delete("/ocr/job/{job_id}")
async def delete_job(job_id: str):
    """
    작업 완료 후 파일 및 결과 삭제 (보안)
    """
    job = job_store.pop(job_id, None)
    if not job:
        raise HTTPException(status_code=404, detail="존재하지 않는 job_id입니다.")

    # 업로드 파일 삭제
    for ext in [".pdf", ".docx", ".doc"]:
        path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")
        if os.path.exists(path):
            os.remove(path)

    return {"message": "삭제 완료"}


@app.get("/ocr/extract/{job_id}")
async def extract_contract_fields(job_id: str):
    """
    OCR 완료된 텍스트에서 계약서 필드 자동 추출
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="존재하지 않는 job_id입니다.")
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"아직 처리 중입니다. 상태: {job['status']}")

    fields = extract_fields(job["result"])
    return {
        "job_id": job_id,
        "fields": fields,
        "raw_text": job["result"]
    }