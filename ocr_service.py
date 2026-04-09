import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from docx import Document
from concurrent.futures import ThreadPoolExecutor

from job_store import job_store


def ocr_page(args):
    """단일 페이지 OCR 처리"""
    i, image, file_path = args
    img_path = f"{file_path}_page_{i}.png"
    image.save(img_path, "PNG")

    # Tesseract OCR (한국어 + 영어)
    text = pytesseract.image_to_string(
        Image.open(img_path),
        lang="kor+eng",
        config="--psm 3"
    )

    os.remove(img_path)
    return i, text.strip()


def process_pdf(job_id: str, file_path: str):
    """
    PDF → 페이지별 이미지 변환 → Tesseract OCR (병렬처리)
    """
    try:
        job_store[job_id]["status"] = "processing"

        # PDF → 이미지 변환 (앞 5페이지만)
        images = convert_from_path(file_path, dpi=150, last_page=5)

        # 병렬 처리 (2개로 제한)
        args = [(i, image, file_path) for i, image in enumerate(images)]
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(ocr_page, args))

        # 페이지 순서대로 정렬
        results.sort(key=lambda x: x[0])
        full_text = [f"[페이지 {i + 1}]\n{text}" for i, text in results]

        job_store[job_id]["status"] = "done"
        job_store[job_id]["result"] = "\n\n".join(full_text)

    except Exception as e:
        job_store[job_id]["status"] = "error"
        job_store[job_id]["error"] = str(e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def process_word(job_id: str, file_path: str):
    """
    Word(.docx) → python-docx로 텍스트 직접 추출
    """
    try:
        job_store[job_id]["status"] = "processing"

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs)

        job_store[job_id]["status"] = "done"
        job_store[job_id]["result"] = full_text

    except Exception as e:
        job_store[job_id]["status"] = "error"
        job_store[job_id]["error"] = str(e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)