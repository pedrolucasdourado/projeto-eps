-- Cadastros auxiliares do módulo ACBA

CREATE TABLE ufs (
    id          SERIAL PRIMARY KEY,
    sigla       VARCHAR(8) NOT NULL UNIQUE,
    nome        VARCHAR(160) NOT NULL,
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cidades (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(180) NOT NULL,
    uf_id       INTEGER NOT NULL REFERENCES ufs(id),
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (nome, uf_id)
);

CREATE INDEX idx_cidades_uf ON cidades (uf_id);

CREATE TABLE unidades_responsaveis (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(220) NOT NULL,
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE delegacias (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(220) NOT NULL,
    unidade_id      INTEGER REFERENCES unidades_responsaveis(id),
    cidade_id       INTEGER REFERENCES cidades(id),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_delegacias_unidade ON delegacias (unidade_id);
CREATE INDEX idx_delegacias_cidade ON delegacias (cidade_id);

CREATE TABLE tipos_procedimento (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(180) NOT NULL UNIQUE,
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE autoridades_policiais (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(220) NOT NULL,
    matricula       VARCHAR(80),
    delegacia_id    INTEGER REFERENCES delegacias(id),
    unidade_id      INTEGER REFERENCES unidades_responsaveis(id),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_autoridades_delegacia ON autoridades_policiais (delegacia_id);
CREATE INDEX idx_autoridades_unidade ON autoridades_policiais (unidade_id);

CREATE TABLE escrivaos (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(220) NOT NULL,
    delegacia_id    INTEGER REFERENCES delegacias(id),
    unidade_id      INTEGER REFERENCES unidades_responsaveis(id),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_escrivaos_delegacia ON escrivaos (delegacia_id);
CREATE INDEX idx_escrivaos_unidade ON escrivaos (unidade_id);

CREATE TABLE membros_equipe_operacional (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(220) NOT NULL,
    matricula       VARCHAR(80) NOT NULL,
    funcao_padrao   VARCHAR(120),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (matricula)
);

CREATE TABLE condutores_operacao (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(220) NOT NULL,
    matricula   VARCHAR(80),
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

