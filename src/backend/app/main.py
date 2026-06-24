from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import acba, auth, cadastros, materiais, users

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


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'none'; "
        "object-src 'none';"
    )
    return response


app.include_router(auth.router, prefix="/api/auth")
app.include_router(cadastros.router, prefix="/api/cadastros", tags=["Cadastros"])
app.include_router(acba.router, prefix="/api/acba", tags=["ACBA"])
app.include_router(materiais.router, prefix="/api/acba", tags=["Materiais"])
app.include_router(users.router, prefix="/api/users", tags=["Usuários"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Assistente de Apreensão Inteligente",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
