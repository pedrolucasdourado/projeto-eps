from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import acba, auth, cadastros, materiais

app = FastAPI(
    title="Assistente de Apreensão Inteligente",
    version="0.1.0",
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(cadastros.router, prefix="/api/cadastros", tags=["Cadastros"])
app.include_router(acba.router, prefix="/api/acba", tags=["ACBA"])
app.include_router(materiais.router, prefix="/api/acba", tags=["Materiais"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
