import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_service import extract_text_from_pdf

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 15
ALLOWED_TYPES = ["application/pdf"]


@router.post("/upload")
async def upload_notes(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    safe_name = os.path.basename(file.filename or "uploaded.pdf")
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB.")

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    try:
        text = extract_text_from_pdf(file_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted. The PDF may be image-based (scanned). Please use a text-based PDF."
        )

    return {
        "filename": safe_name,
        "extracted_text": text,
        "preview": text[:500],
        "total_characters": len(text),
        "estimated_words": len(text.split()),
        "message": "Notes uploaded and extracted successfully."
    }