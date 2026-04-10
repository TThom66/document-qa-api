import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from ai import answer_question
import models, schemas
from database import engine, get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health_check():
    logger.info("Health check called")
    return {"status": "ok"}

@app.post("/documents", response_model=schemas.DocumentResponse)
def create_document(doc: schemas.DocumentCreate, db: Session = Depends(get_db)):
    db_doc = models.Document(title=doc.title, content=doc.content)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    logger.info(f"Document created: id={db_doc.id}, title={db_doc.title}")
    return db_doc

@app.get("/documents/{doc_id}", response_model=schemas.DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        logger.warning(f"Document not found: id={doc_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    logger.info(f"Document retrieved: id={doc_id}")
    return doc

@app.post("/documents/{doc_id}/ask", response_model=schemas.QuestionResponse)
def ask_question(doc_id: int, request: schemas.QuestionRequest, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        logger.warning(f"Ask attempted on missing document: id={doc_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    logger.info(f"Question asked on document {doc_id}: {request.question}")
    answer = answer_question(doc.content, request.question)
    
    return {
        "document_id": doc_id,
        "question": request.question,
        "answer": answer
    }
