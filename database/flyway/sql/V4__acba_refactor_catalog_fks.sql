-- ACBA vinculado aos cadastros auxiliares + equipe (N:N)

DROP TABLE IF EXISTS acba_records CASCADE;

CREATE TABLE acba_records (
    id                      SERIAL PRIMARY KEY,
    numero_auto             VARCHAR(80) NOT NULL UNIQUE,
    unidade_id              INTEGER NOT NULL REFERENCES unidades_responsaveis(id),
    delegacia_id            INTEGER NOT NULL REFERENCES delegacias(id),
    cidade_id               INTEGER NOT NULL REFERENCES cidades(id),
    data_lavratura          DATE NOT NULL,
    hora_lavratura          TIME NOT NULL,
    autoridade_id           INTEGER NOT NULL REFERENCES autoridades_policiais(id),
    escrivao_id             INTEGER NOT NULL REFERENCES escrivaos(id),
    tipo_procedimento_id    INTEGER NOT NULL REFERENCES tipos_procedimento(id),
    procedimento_numero     VARCHAR(120) NOT NULL,
    fundamento_legal        TEXT NOT NULL,
    endereco_busca          TEXT NOT NULL,
    alvo_busca              VARCHAR(220) NOT NULL,
    condutor_id             INTEGER NOT NULL REFERENCES condutores_operacao(id),
    assinatura_responsavel  VARCHAR(220) NOT NULL,
    observacoes             TEXT NOT NULL DEFAULT '',
    testemunhas             JSONB NOT NULL DEFAULT '[]'::jsonb,
    objetos_arrecadados     JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_by_user_id      INTEGER NOT NULL REFERENCES users(id),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_acba_numero ON acba_records (numero_auto);
CREATE INDEX idx_acba_data ON acba_records (data_lavratura);
CREATE INDEX idx_acba_unidade ON acba_records (unidade_id);
CREATE INDEX idx_acba_delegacia ON acba_records (delegacia_id);

CREATE TABLE acba_equipe_membros (
    acba_id     INTEGER NOT NULL REFERENCES acba_records(id) ON DELETE CASCADE,
    membro_id   INTEGER NOT NULL REFERENCES membros_equipe_operacional(id),
    PRIMARY KEY (acba_id, membro_id)
);

CREATE INDEX idx_acba_equipe_membro ON acba_equipe_membros (membro_id);
