"""
FastAPI Upload Service for PDF Files
Handles file uploads and manages processed_states.json for chunk metadata
"""

import os
import io
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import PyPDF2

# Configuration
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# FastAPI app
app = FastAPI(
    title="Stockreport PDF Upload Service",
    description="Handles PDF uploads and chunk metadata management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class UploadResponse(BaseModel):
    fileId: str
    pages: Optional[int] = None
    filename: str
    uploadedAt: str


class ChunkInfo(BaseModel):
    chunk_id: str
    page: int
    bbox_norm: List[float]  # [left, top, right, bottom] normalized 0-1
    label: Optional[str] = None


class ProcessedState(BaseModel):
    file_id: str
    page_count: int
    has_bbox: bool = False
    chunks_content: Dict[str, Dict[str, Any]] = {}


# Helper functions
def get_pdf_page_count(file_path: Path) -> int:
    """Extract page count from PDF file"""
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return len(pdf_reader.pages)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 0


def create_processed_state(file_id: str, page_count: int) -> ProcessedState:
    """Create initial processed state"""
    return ProcessedState(
        file_id=file_id,
        page_count=page_count,
        has_bbox=False,
        chunks_content={}
    )


def save_processed_state(state: ProcessedState) -> None:
    """Save processed state to JSON file"""
    file_path = PROCESSED_DIR / f"{state.file_id}_processed_states.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(state.dict(), f, ensure_ascii=False, indent=2)


def load_processed_state(file_id: str) -> Optional[ProcessedState]:
    """Load processed state from JSON file"""
    file_path = PROCESSED_DIR / f"{file_id}_processed_states.json"
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return ProcessedState(**data)
    except Exception as e:
        print(f"Error loading processed state: {e}")
        return None


# API Endpoints
@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and create initial processed state
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # Generate unique file ID
    file_id = f"{uuid.uuid4().hex}_{Path(file.filename).stem}"
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    
    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get page count
    page_count = get_pdf_page_count(file_path)
    
    # Create and save initial processed state
    processed_state = create_processed_state(file_id, page_count)
    save_processed_state(processed_state)
    
    return UploadResponse(
        fileId=file_id,
        pages=page_count if page_count > 0 else None,
        filename=file.filename,
        uploadedAt=datetime.now().isoformat()
    )


@app.get("/chunks/{file_id}", response_model=List[ChunkInfo])
async def get_chunks(file_id: str):
    """
    Get chunk information for a file
    Returns empty array if no chunks are processed yet
    """
    # Load processed state
    state = load_processed_state(file_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # If no bbox data yet, return empty array
    if not state.has_bbox or not state.chunks_content:
        return []
    
    # Convert chunks to response format
    chunks = []
    for chunk_id, chunk_data in state.chunks_content.items():
        if 'bbox_norm' in chunk_data:
            chunks.append(ChunkInfo(
                chunk_id=chunk_id,
                page=chunk_data.get('page', 0),
                bbox_norm=chunk_data.get('bbox_norm', [0, 0, 0, 0]),
                label=chunk_data.get('label')
            ))
    
    return chunks


@app.get("/file/{file_id}/download")
async def download_file(file_id: str):
    """Download the uploaded PDF file"""
    import urllib.parse
    import os
    
    print(f"Download request for file_id: {file_id}")
    
    # Try multiple decoding strategies
    possible_file_ids = [
        file_id,  # Original
        urllib.parse.unquote(file_id),  # URL decoded once
        urllib.parse.unquote(urllib.parse.unquote(file_id)),  # URL decoded twice
    ]
    
    file_path = None
    actual_file_id = None
    
    # Try to find the file with any of the possible file IDs
    for potential_id in possible_file_ids:
        potential_path = UPLOAD_DIR / f"{potential_id}.pdf"
        print(f"Trying file path: {potential_path}")
        if potential_path.exists():
            file_path = potential_path
            actual_file_id = potential_id
            break
    
    # If still not found, try to find any file that contains the base UUID
    if not file_path:
        # Extract UUID part (first 32 characters)
        base_uuid = file_id.split('_')[0] if '_' in file_id else file_id[:32]
        print(f"Searching for files with UUID: {base_uuid}")
        
        for file in UPLOAD_DIR.glob("*.pdf"):
            if file.stem.startswith(base_uuid):
                file_path = file
                actual_file_id = file.stem
                print(f"Found matching file: {file_path}")
                break
    
    if not file_path or not file_path.exists():
        print(f"File not found. Searched paths:")
        for potential_id in possible_file_ids:
            print(f"  - {UPLOAD_DIR / f'{potential_id}.pdf'}")
        
        # List all files in upload directory for debugging
        print("Available files:")
        for file in UPLOAD_DIR.glob("*.pdf"):
            print(f"  - {file.name}")
            
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )
    
    # Read file and return as streaming response
    try:
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
        
        # Use the original filename for the response
        safe_filename = urllib.parse.quote(actual_file_id.split('_', 1)[-1] if '_' in actual_file_id else actual_file_id)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{safe_filename}.pdf",
                "Content-Length": str(len(pdf_content)),
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "upload-api",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Stockreport PDF Upload Service",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload",
            "chunks": "GET /chunks/{file_id}",
            "download": "GET /file/{file_id}/download",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True) 