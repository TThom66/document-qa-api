import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from ai import answer_question
import models, schemas
from database import engine, get_db
from fastapi.middleware.cors import CORSMiddleware
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    logger.info("Health check called")
    return {"status": "ok"}

# --- Auth endpoints ---

@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    db_user = models.User(
        username=user.username,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"New user registered: {db_user.username}")
    return db_user

@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(db_user.id, db_user.username)
    logger.info(f"User logged in: {db_user.username}")
    return {"access_token": token, "token_type": "bearer"}

# --- Document endpoints ---

@app.post("/documents", response_model=schemas.DocumentResponse)
def create_document(
    doc: schemas.DocumentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_doc = models.Document(
        title=doc.title,
        content=doc.content,
        owner_id=current_user.id
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    logger.info(f"Document created: id={db_doc.id} by user={current_user.username}")
    return db_doc

@app.get("/documents/{doc_id}", response_model=schemas.DocumentResponse)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.owner_id == current_user.id
    ).first()
    if not doc:
        logger.warning(f"Document {doc_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/documents", response_model=list[schemas.DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    docs = db.query(models.Document).filter(
        models.Document.owner_id == current_user.id
    ).all()
    logger.info(f"User {current_user.username} listed {len(docs)} documents")
    return docs

@app.post("/documents/{doc_id}/ask", response_model=schemas.QuestionResponse)
def ask_question(
    doc_id: int,
    request: schemas.QuestionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    answer = answer_question(doc.content, request.question)
    logger.info(f"Question asked by {current_user.username} on doc {doc_id}")
    return {"document_id": doc_id, "question": request.question, "answer": answer}