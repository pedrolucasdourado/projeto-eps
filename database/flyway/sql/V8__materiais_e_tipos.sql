-- V8: Materiais apreendidos com especialização parcial exclusiva
--
-- Modelagem ER:
--   * tipos_material               - catálogo gerenciável de tipos (Notebook, Celular, Veículo, ...)
--                                    O campo `tabela_documento` define em qual das duas tabelas
--                                    do template oficial o material aparece (informatica | geral)
--                                    e é assumido automaticamente pelo material a partir do tipo.
--   * acba_materiais               - super-classe (todo material apreendido)
--       └── acba_materiais_informatica (sub-classe 1:1, opcional)
--             campos exclusivos: senha_tipo, senha_texto, senha_padrao_pontos, senha_observacao
--   * acba_material_ia_runs        - histórico/cache das chamadas ao Gemini Vision
--
-- O campo `categoria_docx` em acba_materiais é uma cópia do `tabela_documento`
-- do tipo no momento da inserção (mantida para preservar a numeração caso o
-- catálogo de tipos seja alterado depois). Cada categoria mantém numeração
-- independente em `item_num` via UNIQUE (acba_id, categoria_docx, item_num);
-- o operador pode informar o `item_num` manualmente.
--
-- A coluna histórica `objetos_arrecadados` (JSONB) do acba_records é removida
-- nesta migração; como o sistema está em estágio inicial, dados são limpos
-- pela seed (V99).

ALTER TABLE acba_records DROP COLUMN IF EXISTS objetos_arrecadados;


CREATE TABLE tipos_material (
    id                      SERIAL PRIMARY KEY,
    nome                    VARCHAR(120) NOT NULL UNIQUE,
    tabela_documento        VARCHAR(20) NOT NULL
        CHECK (tabela_documento IN ('informatica','geral')),
    ativo                   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE acba_materiais (
    id                  SERIAL PRIMARY KEY,
    acba_id             INTEGER NOT NULL REFERENCES acba_records(id),
    tipo_id             INTEGER NOT NULL REFERENCES tipos_material(id),
    categoria_docx      VARCHAR(20) NOT NULL
        CHECK (categoria_docx IN ('informatica','geral')),
    item_num            INTEGER NOT NULL CHECK (item_num >= 1),
    descricao           TEXT NOT NULL,
    descricao_ia_raw    TEXT,
    revisado            BOOLEAN NOT NULL DEFAULT FALSE,
    acondicionamento    VARCHAR(160),
    localizacao         TEXT,
    observacao          TEXT,
    ordem               INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (acba_id, categoria_docx, item_num)
);

CREATE INDEX idx_materiais_acba ON acba_materiais (acba_id);
CREATE INDEX idx_materiais_tipo ON acba_materiais (tipo_id);
CREATE INDEX idx_materiais_revisao ON acba_materiais (acba_id) WHERE revisado = FALSE;


-- Sub-classe 1:1 — só existe quando o material é de informática.
CREATE TABLE acba_materiais_informatica (
    material_id          INTEGER PRIMARY KEY
                         REFERENCES acba_materiais(id) ,
    senha_tipo           VARCHAR(20) NOT NULL DEFAULT 'nenhuma'
                         CHECK (senha_tipo IN
                                ('nenhuma','texto','padrao','biometria','desconhecida')),
    senha_texto          VARCHAR(255),
    senha_padrao_pontos  INTEGER[],
    senha_observacao     TEXT,
    -- Consistência interna dos campos de senha
    CHECK (
        (senha_tipo = 'texto'  AND senha_texto IS NOT NULL AND length(senha_texto) >= 1) OR
        (senha_tipo = 'padrao' AND senha_padrao_pontos IS NOT NULL
                              AND array_length(senha_padrao_pontos, 1) BETWEEN 4 AND 9) OR
        (senha_tipo IN ('nenhuma','biometria','desconhecida'))
    )
);


-- Trigger: garante que só material de informática pode ter linha filha.
CREATE OR REPLACE FUNCTION trg_check_material_informatica()
RETURNS TRIGGER AS $$
DECLARE
    cat TEXT;
BEGIN
    SELECT categoria_docx INTO cat FROM acba_materiais WHERE id = NEW.material_id;
    IF cat IS NULL THEN
        RAISE EXCEPTION 'Material % não encontrado', NEW.material_id;
    END IF;
    IF cat <> 'informatica' THEN
        RAISE EXCEPTION
            'Material % está na categoria %, não pode ter especialização informatica',
            NEW.material_id, cat;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chk_material_informatica
BEFORE INSERT OR UPDATE ON acba_materiais_informatica
FOR EACH ROW EXECUTE FUNCTION trg_check_material_informatica();


-- Validação: padrão de bloqueio com pontos no intervalo [1,9] e sem repetição.
-- (CHECK com subquery em array não é permitido em CHECK simples, então usamos trigger.)
CREATE OR REPLACE FUNCTION trg_valida_padrao_pontos()
RETURNS TRIGGER AS $$
DECLARE
    pt INTEGER;
    seen INTEGER[] := ARRAY[]::INTEGER[];
BEGIN
    IF NEW.senha_tipo <> 'padrao' OR NEW.senha_padrao_pontos IS NULL THEN
        RETURN NEW;
    END IF;
    FOREACH pt IN ARRAY NEW.senha_padrao_pontos LOOP
        IF pt < 1 OR pt > 9 THEN
            RAISE EXCEPTION 'Ponto % fora da grade 3x3 (esperado 1..9)', pt;
        END IF;
        IF pt = ANY(seen) THEN
            RAISE EXCEPTION 'Ponto % repetido na sequência do padrão', pt;
        END IF;
        seen := seen || pt;
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chk_padrao_pontos
BEFORE INSERT OR UPDATE ON acba_materiais_informatica
FOR EACH ROW EXECUTE FUNCTION trg_valida_padrao_pontos();


-- Histórico/cache de chamadas ao Gemini Vision.
-- Por (material_id, request_hash) o mesmo conjunto de imagens não é cobrado de novo.
CREATE TABLE acba_material_ia_runs (
    id              SERIAL PRIMARY KEY,
    material_id     INTEGER NOT NULL REFERENCES acba_materiais(id) ,
    modelo          VARCHAR(80) NOT NULL,
    prompt_versao   VARCHAR(40) NOT NULL,
    request_hash    CHAR(64) NOT NULL,
    resposta        TEXT NOT NULL,
    custo_tokens    INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (material_id, request_hash)
);

CREATE INDEX idx_ia_runs_material ON acba_material_ia_runs (material_id);


-- Auditoria: lista materiais "informatica" sem linha filha (defeito de integridade).
CREATE OR REPLACE VIEW vw_materiais_informatica_orfaos AS
SELECT m.id, m.acba_id, m.tipo_id, m.descricao
FROM acba_materiais m
LEFT JOIN acba_materiais_informatica i ON i.material_id = m.id
WHERE m.categoria_docx = 'informatica' AND i.material_id IS NULL;


-- Seed do catálogo de tipos. `tabela_documento` define automaticamente em qual
-- das duas tabelas do auto o material aparece (não é editável por material).
INSERT INTO tipos_material (nome, tabela_documento) VALUES
    ('Notebook',                'informatica'),
    ('Computador desktop',      'informatica'),
    ('Celular',                 'informatica'),
    ('Tablet',                  'informatica'),
    ('HD / SSD externo',        'informatica'),
    ('Pen drive',               'informatica'),
    ('Cartão de memória',       'informatica'),
    ('Roteador / modem',        'informatica'),
    ('Documento',               'geral'),
    ('Veículo',                 'geral'),
    ('Arma de fogo',            'geral'),
    ('Munição',                 'geral'),
    ('Dinheiro em espécie',     'geral'),
    ('Entorpecente',            'geral'),
    ('Outros',                  'geral');
