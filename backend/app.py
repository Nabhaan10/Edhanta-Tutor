import logging
import traceback

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import AnswerResponse, ImageAnswerResponse, ExtractedMetadata, QuestionRequest
from rag.chatbot import ask
from rag.vision_extractor import extract_question
from rag.router import router as question_router
from rag.solver import solve_with_context
from rag.retriever import search_with_threshold
from rag.memory import memory_manager

log = logging.getLogger(__name__)

# ── Allowed image MIME types ──────────────────────────────────────────────────
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Welcome to Edhanta AI Backend API"}


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    try:
        return ask(request.question, request.session_id, request.board)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask-image", response_model=ImageAnswerResponse)
async def ask_image_question(
    image: UploadFile,
    session_id: str = Form(...),
    board: str = Form("CBSE"),
    language: str = Form("English"),
):
    """
    Hybrid image question pipeline.

    Flow
    ----
    1. Vision extraction  — extract question + metadata from the image.
    2. RAG retrieval      — always fetch relevant textbook chunks (formulas,
                            definitions, theory) regardless of question type.
    3. Question routing   — classify as "theory" or "numerical".
    4. Generation:
         theory    → generate_answer() via ask() — strict context-only prompt.
         numerical → solve_with_context()        — reference-augmented solver.
    5. Memory update      — store exchange so follow-up detection works.

    Form fields
    -----------
    image      : JPEG or PNG file upload.
    session_id : Conversation session identifier.
    board      : "CBSE" or "MH" (default: "CBSE").
    language   : Response language hint (default: "English").
    """
    # ── Validate MIME type ────────────────────────────────────────────────────
    content_type = (image.content_type or "").lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{content_type}'. "
                "Please upload a JPEG or PNG image."
            ),
        )

    # ── Read bytes ────────────────────────────────────────────────────────────
    try:
        image_bytes = await image.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="Could not read the uploaded file."
        ) from exc

    # ── Phase 1: Vision extraction ────────────────────────────────────────────
    try:
        extracted = extract_question(image_bytes, content_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=str(exc))

    # ── Phase 2: Route classification ─────────────────────────────────────────
    route = question_router.classify(extracted)

    # ── Phase 3: RAG retrieval (always runs) ──────────────────────────────────
    # Build a richer search query: topic + question gives better chunk recall
    # for both formula lookup (numerical) and concept lookup (theory).
    topic = extracted.get("topic", "") or ""
    q_text = extracted.get("question", "") or ""
    search_query = f"{topic} {q_text}".strip() if topic else q_text

    try:
        rag_results = search_with_threshold(search_query)
    except Exception as exc:
        log.warning("[APP] RAG retrieval failed: %s — proceeding without context.", exc)
        rag_results = {"documents": [[]], "metadatas": [[]]}

    has_context = bool(rag_results["documents"][0])
    context = "\n\n".join(rag_results["documents"][0]) if has_context else ""
    sources: list[str] = (
        list({m["source"] for m in rag_results["metadatas"][0]})
        if has_context else []
    )

    log.info(
        "[APP] route=%s | context_chunks=%d | sources=%d",
        route, len(rag_results["documents"][0]), len(sources),
    )

    # ── Phase 4: Generation ───────────────────────────────────────────────────
    memory = memory_manager.get_memory(session_id)
    history = memory.get_history()

    try:
        if route == "numerical":
            # Reference-augmented solver: uses retrieved formulas/theory as
            # reference material, then reasons freely to solve step-by-step.
            answer = solve_with_context(
                question=q_text,
                context=context,
                marks=extracted.get("marks", "") or "",
                subject=extracted.get("subject", "") or "",
                board=board,
                history=history,
            )
        else:
            # Theory path: strict context-only RAG generation via chatbot.ask().
            # ask() handles its own retrieval + memory internally; we pass the
            # extracted question directly.
            result = ask(q_text, session_id, board)
            answer = result["answer"]
            sources = result["sources"]   # use sources from ask() for theory path

    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))

    # ── Phase 5: Memory update (numerical path only) ──────────────────────────
    # The theory path delegates to ask() which manages memory internally.
    # For the numerical path we update memory here so follow-up detection works.
    if route == "numerical":
        memory.add_user_message(q_text)
        memory.add_assistant_message(answer)

    # ── Build response ────────────────────────────────────────────────────────
    return ImageAnswerResponse(
        answer=answer,
        sources=sources,
        route=route,
        extracted=ExtractedMetadata(
            question=extracted["question"],
            subject=extracted.get("subject") or None,
            topic=extracted.get("topic") or None,
            marks=extracted.get("marks") or None,
            question_type=extracted.get("question_type") or None,
        ),
    )


@app.get("/health")
def health():
    return {"status": "healthy"}