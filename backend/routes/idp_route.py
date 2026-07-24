import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File

# Internal Imports
from auth.role_checker import RoleChecker
from modules.idp import extract_fields
from routes.admin_route import add_audit_log  # ✅ Use the unified function

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
            "timestamp": datetime.utcnow().isoformat()
        })

        return result

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ── In-memory document status store (stub — no DB persistence needed) ─────────
_document_status: dict = {}


@router.patch("/api/documents/{doc_id}/approve")
def approve_document(doc_id: str, payload: dict = Depends(allow_verification_ops)):
    """Officer approves a processed document."""
    _document_status[doc_id] = "approved"
    add_audit_log({
        "user": payload.get("sub", "Unknown"),
        "role": payload.get("role", "N/A"),
        "district": payload.get("district", "Unknown"),
        "action": "Document Approved",
        "file": doc_id,
        "status": "AUTO-VERIFIED",
        "timestamp": datetime.utcnow().isoformat()
    })
    return {"id": doc_id, "status": "approved", "message": "Document approved and synced"}


@router.patch("/api/documents/{doc_id}/flag")
def flag_document(doc_id: str, payload: dict = Depends(allow_verification_ops)):
    """Officer flags a document for human review."""
    _document_status[doc_id] = "flagged"
    add_audit_log({
        "user": payload.get("sub", "Unknown"),
        "role": payload.get("role", "N/A"),
        "district": payload.get("district", "Unknown"),
        "action": "Document Flagged",
        "file": doc_id,
        "status": "FLAGGED",
        "timestamp": datetime.utcnow().isoformat()
    })
    return {"id": doc_id, "status": "flagged", "message": "Document flagged for manual review"}