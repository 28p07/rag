from fastapi import FastAPI, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
import PyPDF2
import pypdf
from io import BytesIO
from datetime import datetime
from app.db import DocumentDB, get_db
from app.rag import process_document, query_rag

app = FastAPI()

@app.on_event("shutdown")
def shutdown_event():
    get_db().close()

async def validate_pdf(file: UploadFile):
    if file.content_type != "application/pdf":
        raise HTTPException(400, f"File '{file.filename}' is not a PDF")
    
    contents = await file.read()
    pdf = pypdf.PdfReader(BytesIO(contents))
    if len(pdf.pages) > 1000:
        raise HTTPException(400, f"PDF exceeds 1000-page limit (pages: {len(pdf.pages)})")
    file.file.seek(0)
    return contents


@app.post("/upload")
async def upload_documents(files: List[UploadFile], db: DocumentDB = Depends(get_db)):
    # Check 20-doc limit
    if db.get_document_count() + len(files) > 20:
        raise HTTPException(400, "Maximum 20 documents allowed")
    
    results = []
    for file in files:
        os.makedirs("data", exist_ok=True)
        temp_path = f"data/{uuid.uuid4()}.pdf"
        try:
            contents = await validate_pdf(file)
            with open(temp_path, "wb") as f:
                f.write(contents)
            
            metadata = process_document(temp_path, file.filename)
            db.add_document(metadata)
            results.append({"filename": file.filename, "status": "success"})
        except HTTPException as e:
            results.append({"filename": file.filename, "status": "failed", "error": e.detail})
        except Exception as e:
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return JSONResponse({"results": results})

@app.get("/query")
async def query(q: str):
    return query_rag(q)

@app.get("/documents")
async def list_documents(db: DocumentDB = Depends(get_db)):
    documents = db.get_all_documents()
    
    # Format datetime for better readability
    for doc in documents:
        doc["upload_time"] = datetime.fromisoformat(doc["upload_time"]).strftime("%Y-%m-%d %H:%M:%S")
    
    return documents