import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from ai import answer_question, answer_question_async
import models, schemas
from database import engine, get_db
from fastapi.middleware.cors import CORSMiddleware
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)
import json
from fastapi.security import OAuth2PasswordRequestForm
import asyncio

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

@app.post("/auth/token", response_model=schemas.TokenResponse)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()
    if not db_user or not verify_password(
        form_data.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials"
        )
    token = create_access_token(db_user.id, db_user.username)
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

@app.post("/templates", response_model=schemas.TemplateResponse)
def create_template(
    template: schemas.TemplateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not template.questions:
        raise HTTPException(
            status_code=400, 
            detail="Template must have at least one question"
        )
    db_template = models.Template(
        title=template.title,
        questions=json.dumps(template.questions),
        owner_id=current_user.id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    logger.info(
        f"Template created: id={db_template.id} "
        f"by user={current_user.username}"
    )
    # Parse questions back for response
    db_template.questions = json.loads(db_template.questions)
    return db_template

@app.get("/templates", response_model=list[schemas.TemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = db.query(models.Template).filter(
        models.Template.owner_id == current_user.id
    ).all()
    for t in templates:
        t.questions = json.loads(t.questions)
    return templates

@app.post("/templates/{template_id}/apply",
    response_model=schemas.TemplateApplyResponse)
async def apply_template(
    template_id: int,
    request: schemas.TemplateApplyRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    template = db.query(models.Template).filter(
        models.Template.id == template_id,
        models.Template.owner_id == current_user.id
    ).first()
    if not template:
        raise HTTPException(
            status_code=404, 
            detail="Template not found"
        )

    doc = db.query(models.Document).filter(
        models.Document.id == request.document_id,
        models.Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(
            status_code=404, 
            detail="Document not found"
        )

    questions = json.loads(template.questions)

    logger.info(
        f"Applying {len(questions)} questions in parallel "
        f"to doc {doc.id}"
    )

    tasks = [
        answer_question_async(doc.content, question)
        for question in questions
    ]
    results = await asyncio.gather(*tasks)

    return {
        "template_title": template.title,
        "document_title": doc.title,
        "results": list(results)
    }