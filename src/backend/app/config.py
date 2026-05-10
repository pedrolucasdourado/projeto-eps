from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://aai:aai_secret@localhost:5432/aai_db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    # localhost e 127.0.0.1 são origens distintas para o navegador — inclua ambas se usar um ou outro.
    cors_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://[::1]:3000"
    )

    # Template DOCX do ACBA (substitua pelo modelo oficial com os mesmos placeholders)
    acba_docx_template_path: str = "/app/templates/acba_template.docx"
    # Comando LibreOffice para conversão DOCX→PDF (vazio = auto: soffice/libreoffice no PATH)
    libreoffice_cmd: str = ""
    # Chave da API do Gemini (obrigatória para o serviço de descrição por IA).
    gemini_api_key: str = ""
    # Modelo do Gemini usado para visão. Sobreescreve via GEMINI_MODEL no .env.
    gemini_model: str = "gemini-2.0-flash"
    # Permite gerar PDF mesmo com materiais com revisão pendente (default: False = bloqueia)
    acba_permitir_pdf_com_pendencia: bool = False


settings = Settings()
