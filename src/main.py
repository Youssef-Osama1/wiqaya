from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.registry import all_doc_specs
from src.helpers.config import get_settings
from src.routes import data as data_routes
from src.routes import evaluation as evaluation_routes
from src.routes import nlp as nlp_routes
from src.stores.bm25_factory import build_bm25_retriever
from src.stores.embedding_factory import get_embeddings
from src.stores.llm_factory import get_llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.embeddings = get_embeddings(settings)
    app.state.llm = get_llm(settings)
    app.state.bm25_retriever = build_bm25_retriever(
        [spec.doc_key for spec in all_doc_specs()], k=settings.DEFAULT_TOP_K
    )
    yield


APP_TITLE = "Wiqaya"

app = FastAPI(title=APP_TITLE, lifespan=lifespan)

app.include_router(data_routes.router)
app.include_router(nlp_routes.router)
app.include_router(evaluation_routes.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": f"Internal server error: {exc}"})


@app.get("/")
def root() -> dict:
    return {"app": APP_TITLE, "status": "ok"}


_cors_settings = get_settings()
# Wrapping the ASGI app externally (rather than app.add_middleware(CORSMiddleware, ...))
# is required, not stylistic: Starlette special-cases an Exception/500 handler to attach
# to ServerErrorMiddleware, which sits OUTSIDE every middleware added via add_middleware.
# A CORS layer added that way never sees the response for an unhandled exception, so the
# browser reports a bare connection failure instead of a readable error. Wrapping here
# makes CORS the true outermost layer, catching every response including that one.
_fastapi_app = app
app = CORSMiddleware(
    app=_fastapi_app,
    allow_origins=[origin.strip() for origin in _cors_settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# tests and tooling reach for `app.state` (e.g. TestClient(app).app.state.llm = ...) —
# alias it onto the wrapper so it still works now that `app` is the CORS layer, not the
# FastAPI instance directly. Request handlers are unaffected: `request.app` is set by
# Starlette's router to the original FastAPI instance regardless of outer ASGI wrapping.
app.state = _fastapi_app.state
