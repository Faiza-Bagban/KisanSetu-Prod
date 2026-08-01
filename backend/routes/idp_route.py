import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

# Internal Imports
from auth.role_checker import RoleChecker
from modules.idp import extract_fields
from routes.admin_route import add_audit_log  # ✅ Use the unified function
from database import get_db
from models.document_model import Document

router = APIRouter()

allow_verification_ops = RoleChecker(["farmer", "field_officer", "district_officer", "admin"])

@router.post("/api/idp/extract")
def extract_document(
    file: UploadFile = File(...), 
    payload: dict = Depends(allow_verification_ops)
):
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    safe_filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(temp_dir, safe_filename)

    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        result = extract_fields(file_path)

        # ✅ Log via the unified helper function
        add_audit_log({
            "user": payload.get("sub", "Unknown"),
            "role": payload.get("role", "N/A"),
            "district": payload.get("district", "Unknown"),
            "action": "IDP Extraction",
            "file": file.filename,
            "status": (result or {}).get("status", "processed"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return result

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ── Document approve/flag — persisted to real DB (Document.verification_status) ──

@router.patch("/api/documents/{doc_id}/approve")
def approve_document(
    doc_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(allow_verification_ops),
):
    """Officer approves a processed document — writes to DB, not in-memory."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.verification_status = "Verified"
    db.add(doc)
    db.commit()

    add_audit_log({
        "user": payload.get("sub", "Unknown"),
        "role": payload.get("role", "N/A"),
        "district": payload.get("district", "Unknown"),
        "action": "Document Approved",
        "file": str(doc_id),
        "status": "AUTO-VERIFIED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"id": doc_id, "status": "Verified", "message": "Document approved and synced"}


@router.patch("/api/documents/{doc_id}/flag")
def flag_document(
    doc_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(allow_verification_ops),
):
    """Officer flags a document for human review — writes to DB, not in-memory."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.verification_status = "Rejected"
    db.add(doc)
    db.commit()

    add_audit_log({
        "user": payload.get("sub", "Unknown"),
        "role": payload.get("role", "N/A"),
        "district": payload.get("district", "Unknown"),
        "action": "Document Flagged",
        "file": str(doc_id),
        "status": "FLAGGED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"id": doc_id, "status": "Rejected", "message": "Document flagged for manual review"}