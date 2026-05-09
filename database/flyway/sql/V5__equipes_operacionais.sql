-- Equipes operacionais: cada ACBA vincula a 1 equipe; policiais (membros) podem
-- pertencer a 0, 1 ou mais equipes (N:N).

CREATE TABLE equipes_operacionais (
    id          SERIAL PRIMARY KEY,
    numero      VARCHAR(40) NOT NULL UNIQUE,
    nome        VARCHAR(220),
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE equipe_operacional_membros (
    equipe_id   INTEGER NOT NULL REFERENCES equipes_operacionais(id) ON DELETE CASCADE,
    membro_id   INTEGER NOT NULL REFERENCES membros_equipe_operacional(id) ON DELETE CASCADE,
    PRIMARY KEY (equipe_id, membro_id)
);

CREATE INDEX idx_equipe_op_membros_membro ON equipe_operacional_membros (membro_id);

ALTER TABLE acba_records ADD COLUMN equipe_id INTEGER REFERENCES equipes_operacionais(id);

DROP TABLE acba_equipe_membros;

ALTER TABLE acba_records ALTER COLUMN equipe_id SET NOT NULL;

CREATE INDEX idx_acba_equipe ON acba_records (equipe_id);
