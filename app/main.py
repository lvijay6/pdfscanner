import io
import os
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.services.ocr import SmartScannerService, AIOCREngine
from app.services.classifier import AIDocumentClassifier
from app.services.extractor import AIDataExtractor
from app.services.pdf_utils import PDFUtilitiesService
from app.services.rag_chat import AIRAGChatService
from app.services.expense import ExpenseManagerService
from app.services.workflow import EnterpriseWorkflowService

app = FastAPI(
    title="AI PDF Scanner & Document Intelligence Platform",
    description="Product Specification (2026) Implementation - Modules 1 through 13",
    version="2.0.0"
)

# Request Pydantic Models
class ChatRequest(BaseModel):
    text_content: str
    question: str

class SummarizeRequest(BaseModel):
    text_content: str
    summary_type: Optional[str] = "Executive Summary"

class TranslateRequest(BaseModel):
    text_content: str
    target_language: str

class VoiceCommandRequest(BaseModel):
    transcript: str
    text_content: Optional[str] = ""

class ExpenseCreateRequest(BaseModel):
    vendor: str
    amount: float
    category: str
    date: Optional[str] = None
    gst_included: Optional[bool] = True

class WorkflowCreateRequest(BaseModel):
    document_name: str
    category: str
    uploader: Optional[str] = "Enterprise User"

class WorkflowUpdateRequest(BaseModel):
    workflow_id: str
    status: str
    user: Optional[str] = "Manager"

class CloudSyncRequest(BaseModel):
    provider: str
    filename: str

# Module 1 & 2: Scanner & OCR
@app.post("/api/scan/enhance")
async def enhance_scanned_image(file: UploadFile = File(...)):
    contents = await file.read()
    result = SmartScannerService.enhance_image(contents)
    return result

@app.post("/api/ocr/process")
async def process_ocr(
    file: UploadFile = File(...),
    language: str = Form("English"),
    is_handwritten: bool = Form(False)
):
    contents = await file.read()
    ocr_res = AIOCREngine.extract_text_from_pdf(contents, language=language, is_handwritten=is_handwritten)
    classification_res = AIDocumentClassifier.classify_document(ocr_res["extracted_text"], filename=file.filename or "")
    extraction_res = AIDataExtractor.extract_data(classification_res["document_type"], ocr_res["extracted_text"])

    return {
        "filename": file.filename,
        "ocr": ocr_res,
        "classification": classification_res,
        "extraction": extraction_res
    }

# Module 3 & 4: Classification & Extraction
@app.post("/api/extract")
async def extract_structured_data(
    text_content: str = Form(...),
    document_type: str = Form("Invoice"),
    export_format: str = Form("json")
):
    extracted = AIDataExtractor.extract_data(document_type, text_content)
    formatted = AIDataExtractor.export_data(extracted, export_format)

    if export_format.lower() in ["csv", "excel", "tsv"]:
        return Response(content=formatted, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=extracted_{document_type}.csv"})
    return JSONResponse(content=extracted)

# Module 5, 6, 7 & 8: Summary, RAG Chat, Translation & Voice Assistant
@app.post("/api/ai/summarize")
async def summarize_document(req: SummarizeRequest):
    return AIRAGChatService.generate_summary(req.text_content, req.summary_type)

@app.post("/api/ai/chat")
async def chat_with_pdf_endpoint(req: ChatRequest):
    return AIRAGChatService.chat_with_pdf(req.text_content, req.question)

@app.post("/api/ai/translate")
async def translate_document_endpoint(req: TranslateRequest):
    return AIRAGChatService.translate_document(req.text_content, req.target_language)

@app.post("/api/ai/voice-command")
async def voice_command_endpoint(req: VoiceCommandRequest):
    return AIRAGChatService.process_voice_command(req.transcript, req.text_content)

# Module 9: PDF Utilities
@app.post("/api/pdf/merge")
async def merge_pdfs_endpoint(files: List[UploadFile] = File(...)):
    pdf_bytes_list = []
    for file in files:
        pdf_bytes_list.append(await file.read())
    merged_bytes = PDFUtilitiesService.merge_pdfs(pdf_bytes_list)
    return StreamingResponse(io.BytesIO(merged_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=merged_document.pdf"})

@app.post("/api/pdf/split")
async def split_pdf_endpoint(file: UploadFile = File(...)):
    contents = await file.read()
    pages = PDFUtilitiesService.split_pdf(contents)
    return {"total_pages": len(pages), "message": f"PDF successfully split into {len(pages)} standalone page files."}

@app.post("/api/pdf/reorder-rotate")
async def reorder_rotate_endpoint(
    file: UploadFile = File(...),
    rotation: int = Form(90)
):
    contents = await file.read()
    processed_bytes = PDFUtilitiesService.reorder_or_rotate_pages(contents, rotation=rotation)
    return StreamingResponse(io.BytesIO(processed_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=rotated_document.pdf"})

@app.post("/api/pdf/protect")
async def protect_pdf_endpoint(
    file: UploadFile = File(...),
    password: str = Form(...)
):
    contents = await file.read()
    protected_bytes = PDFUtilitiesService.protect_pdf(contents, password)
    return StreamingResponse(io.BytesIO(protected_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=protected_document.pdf"})

@app.post("/api/pdf/watermark")
async def watermark_pdf_endpoint(
    file: UploadFile = File(...),
    watermark_text: str = Form("CONFIDENTIAL")
):
    contents = await file.read()
    watermarked_bytes = PDFUtilitiesService.add_watermark(contents, watermark_text)
    return StreamingResponse(io.BytesIO(watermarked_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=watermarked_document.pdf"})

@app.post("/api/pdf/digital-signature")
async def digital_signature_endpoint(
    file: UploadFile = File(...),
    signer_name: str = Form("Enterprise Authority")
):
    contents = await file.read()
    res = PDFUtilitiesService.digital_signature(contents, signer_name)
    return {
        "signer": res["signer"],
        "encryption": res["encryption"],
        "timestamp": res["timestamp"],
        "status": res["status"]
    }

# Module 10: Expense Management
@app.get("/api/expense/report")
async def get_expense_report():
    return ExpenseManagerService.get_summary_report()

@app.post("/api/expense/add")
async def add_expense_endpoint(req: ExpenseCreateRequest):
    return ExpenseManagerService.add_expense(req.vendor, req.amount, req.category, req.date, req.gst_included)

# Module 11 & 12: Enterprise Workflow & Cloud Sync
@app.get("/api/workflow/list")
async def list_workflows_endpoint():
    return EnterpriseWorkflowService.list_workflows()

@app.post("/api/workflow/create")
async def create_workflow_endpoint(req: WorkflowCreateRequest):
    return EnterpriseWorkflowService.create_workflow(req.document_name, req.category, req.uploader)

@app.post("/api/workflow/update-status")
async def update_workflow_status_endpoint(req: WorkflowUpdateRequest):
    return EnterpriseWorkflowService.update_workflow_status(req.workflow_id, req.status, req.user)

@app.get("/api/workflow/audit-logs")
async def get_audit_logs_endpoint():
    return EnterpriseWorkflowService.get_audit_logs()

@app.post("/api/cloud/sync")
async def sync_cloud_endpoint(req: CloudSyncRequest):
    return EnterpriseWorkflowService.sync_to_cloud(req.provider, req.filename)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return "<h1>AI PDF Scanner Platform Server Running</h1>"
