import io
import pytest
from fastapi.testclient import TestClient
import pypdf
from app.main import app

client = TestClient(app)

def create_sample_pdf_bytes(text: str = "INVOICE #INV-2026-9900\nVendor: Acme Cloud Solutions\nTotal Amount: $1,770.00") -> bytes:
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

def test_enhance_scanned_image():
    response = client.post("/api/scan/enhance", files={"file": ("sample.jpg", b"fake image content", "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "auto_crop" in data["applied_enhancements"]

def test_ocr_and_classification():
    pdf_bytes = create_sample_pdf_bytes()
    response = client.post(
        "/api/ocr/process",
        files={"file": ("invoice.pdf", pdf_bytes, "application/pdf")},
        data={"language": "English", "is_handwritten": "false"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "ocr" in data
    assert "classification" in data
    assert "extraction" in data
    assert data["classification"]["document_type"] in ["Invoice", "General PDF", "PAN Card"]

def test_ai_summarization():
    response = client.post(
        "/api/ai/summarize",
        json={"text_content": "Invoice #INV-2026-8892\nVendor: Acme Cloud Solutions\nTotal: $1,770.00", "summary_type": "Executive Summary"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert len(data["action_items"]) > 0

def test_chat_with_pdf():
    response = client.post(
        "/api/ai/chat",
        json={
            "text_content": "Invoice #INV-2026-8892\nVendor: Acme Cloud Solutions\nTotal Amount: $1,770.00\nDue Date: 2026-04-15",
            "question": "What is the total amount?"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "1,770.00" in data["answer"] or "total amount" in data["answer"].lower()

def test_translation():
    response = client.post(
        "/api/ai/translate",
        json={"text_content": "Invoice processed successfully.", "target_language": "Tamil"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["target_language"] == "Tamil"
    assert "translated_text" in data

def test_voice_command():
    response = client.post(
        "/api/ai/voice-command",
        json={"transcript": "summarize document", "text_content": "Contract details for enterprise user."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recognized_intent"] == "summarize"

def test_pdf_merge():
    pdf1 = create_sample_pdf_bytes("PDF 1 Content")
    pdf2 = create_sample_pdf_bytes("PDF 2 Content")
    response = client.post(
        "/api/pdf/merge",
        files=[("files", ("p1.pdf", pdf1, "application/pdf")), ("files", ("p2.pdf", pdf2, "application/pdf"))]
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

def test_expense_ledger():
    report = client.get("/api/expense/report")
    assert report.status_code == 200
    assert report.json()["total_expenses_count"] >= 3

    add_res = client.post(
        "/api/expense/add",
        json={"vendor": "GitHub", "amount": 100.0, "category": "Software", "gst_included": True}
    )
    assert add_res.status_code == 200
    assert add_res.json()["vendor"] == "GitHub"

def test_enterprise_workflow():
    list_res = client.get("/api/workflow/list")
    assert list_res.status_code == 200

    create_res = client.post(
        "/api/workflow/create",
        json={"document_name": "New_Contract.pdf", "category": "Business Documents", "uploader": "Alice"}
    )
    assert create_res.status_code == 200
    assert create_res.json()["document_name"] == "New_Contract.pdf"

    sync_res = client.post(
        "/api/cloud/sync",
        json={"provider": "AWS S3", "filename": "New_Contract.pdf"}
    )
    assert sync_res.status_code == 200
    assert sync_res.json()["cloud_provider"] == "AWS S3"
