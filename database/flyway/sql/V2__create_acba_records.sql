CREATE TABLE acba_records (
    id SERIAL PRIMARY KEY,
    numero_auto VARCHAR(80) NOT NULL UNIQUE,
    unidade_responsavel VARCHAR(180) NOT NULL,
    delegacia VARCHAR(180) NOT NULL,
    cidade_uf VARCHAR(120) NOT NULL,
    data_lavratura DATE NOT NULL,
    hora_lavratura TIME NOT NULL,
    autoridade_policial VARCHAR(180) NOT NULL,
    escrivao_responsavel VARCHAR(180) NOT NULL,
    tipo_procedimento VARCHAR(80) NOT NULL,
    procedimento_numero VARCHAR(120) NOT NULL,
    fundamento_legal TEXT NOT NULL,
    endereco_busca TEXT NOT NULL,
    alvo_busca VARCHAR(180) NOT NULL,
    equipe_operacional JSONB NOT NULL DEFAULT '[]'::jsonb,
    testemunhas JSONB NOT NULL DEFAULT '[]'::jsonb,
    objetos_arrecadados JSONB NOT NULL DEFAULT '[]'::jsonb,
    observacoes TEXT NOT NULL DEFAULT '',
    condutor_operacao VARCHAR(180) NOT NULL,
    assinatura_responsavel VARCHAR(180) NOT NULL,
    created_by_user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_acba_records_numero_auto ON acba_records (numero_auto);
CREATE INDEX idx_acba_records_data_lavratura ON acba_records (data_lavratura);
