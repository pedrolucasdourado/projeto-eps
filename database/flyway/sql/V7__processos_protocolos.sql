-- V7: cadastro de processos e ajustes no ACBA.
-- Regras:
--   * O número do processo é o identificador (PK natural) da tabela processos.
--   * Um processo pode ter vários ACBAs vinculados.
--   * O número do protocolo é exclusivo de cada ACBA (não tem cadastro próprio):
--     fica como coluna no acba_records, com UNIQUE para evitar duplicação.
--   * O campo numero_auto deixa de existir no ACBA — a identificação passa a ser
--     processo + protocolo.

CREATE TABLE processos (
    numero      VARCHAR(60) PRIMARY KEY,
    descricao   VARCHAR(220),
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Refactor do ACBA. Como o sistema está em estágio inicial e numero_auto era
-- NOT NULL UNIQUE, limpa-se eventuais registros existentes antes da troca de
-- schema. A migração V99 (seeds) volta a popular dados de teste já no novo
-- formato.
DELETE FROM acba_records;

ALTER TABLE acba_records DROP COLUMN numero_auto;

ALTER TABLE acba_records
    ADD COLUMN processo_numero VARCHAR(60) NOT NULL
        REFERENCES processos(numero) ON UPDATE CASCADE,
    ADD COLUMN protocolo_numero VARCHAR(60) NOT NULL;

ALTER TABLE acba_records
    ADD CONSTRAINT uq_acba_protocolo UNIQUE (protocolo_numero);

CREATE INDEX idx_acba_processo ON acba_records (processo_numero);
