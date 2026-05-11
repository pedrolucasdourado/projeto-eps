-- V10: testemunhas normalizadas (super-classe + parcial exclusiva para
-- arrombamento) e qualificação do morador presente.
--
-- Estrutura final:
--
--   acba_records
--     + morador_nome, morador_cpf, morador_rg, morador_filiacao,
--       morador_telefone  (qualificação obrigatória apenas quando o morador
--       NÃO estava ausente — i.e., morador_ausente_245_4 = FALSE).
--
--   acba_testemunhas  (super-classe — toda testemunha do auto)
--     id, acba_id, nome, cpf, rg, filiacao, endereco, cidade, telefone,
--     tipo IN ('geral','arrombamento'), ordem.
--     - cidade e telefone só são preenchidos para testemunhas gerais.
--
--   acba_testemunhas_arrombamento  (sub-classe 1:1, parcial exclusiva)
--     testemunha_id PK FK, observacoes
--     - Mesmo padrão de acba_materiais / acba_materiais_informatica:
--       só existe quando a super-classe tem tipo='arrombamento';
--       o trigger trg_check_testemunha_arrombamento garante isso.
--
-- A coluna histórica acba_records.testemunhas (JSONB) é migrada e removida.
-- Como o sistema está em estágio inicial, registros antigos recebem
-- placeholders ('Não informado') nos campos novos NOT NULL.


CREATE TABLE acba_testemunhas (
    id          SERIAL PRIMARY KEY,
    acba_id     INTEGER NOT NULL REFERENCES acba_records(id) ON DELETE CASCADE,
    nome        VARCHAR(180) NOT NULL,
    cpf         VARCHAR(20)  NOT NULL,
    rg          VARCHAR(40)  NOT NULL,
    filiacao    VARCHAR(220) NOT NULL,
    endereco    TEXT         NOT NULL,
    cidade      VARCHAR(120),
    telefone    VARCHAR(40),
    tipo        VARCHAR(20)  NOT NULL DEFAULT 'geral'
                CHECK (tipo IN ('geral', 'arrombamento')),
    ordem       INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(nome))     >= 2),
    CHECK (length(trim(cpf))      >= 3),
    CHECK (length(trim(rg))       >= 1),
    CHECK (length(trim(filiacao)) >= 2),
    CHECK (length(trim(endereco)) >= 5)
);

CREATE INDEX idx_acba_testemunhas_acba ON acba_testemunhas (acba_id);
CREATE INDEX idx_acba_testemunhas_tipo ON acba_testemunhas (acba_id, tipo);


-- Sub-classe 1:1 parcial exclusiva. Os campos comuns (cpf, rg, filiação,
-- endereço) vivem na super-classe. Aqui só fica o que é EXCLUSIVO da
-- testemunha de arrombamento.
CREATE TABLE acba_testemunhas_arrombamento (
    testemunha_id  INTEGER PRIMARY KEY
                   REFERENCES acba_testemunhas(id) ON DELETE CASCADE,
    observacoes    TEXT NOT NULL DEFAULT ''
);


-- Trigger: garante que só testemunhas tipo='arrombamento' podem ter linha
-- filha (mesmo padrão de trg_check_material_informatica).
CREATE OR REPLACE FUNCTION trg_check_testemunha_arrombamento()
RETURNS TRIGGER AS $$
DECLARE
    t_tipo TEXT;
BEGIN
    SELECT tipo INTO t_tipo FROM acba_testemunhas WHERE id = NEW.testemunha_id;
    IF t_tipo IS NULL THEN
        RAISE EXCEPTION 'Testemunha % não encontrada', NEW.testemunha_id;
    END IF;
    IF t_tipo <> 'arrombamento' THEN
        RAISE EXCEPTION
            'Testemunha % está no tipo %, não pode ter especialização arrombamento',
            NEW.testemunha_id, t_tipo;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chk_testemunha_arrombamento
BEFORE INSERT OR UPDATE ON acba_testemunhas_arrombamento
FOR EACH ROW EXECUTE FUNCTION trg_check_testemunha_arrombamento();


-- Auditoria: lista testemunhas tipo='arrombamento' sem linha filha (defeito
-- de integridade — análogo a vw_materiais_informatica_orfaos).
CREATE OR REPLACE VIEW vw_testemunhas_arrombamento_orfas AS
SELECT t.id, t.acba_id, t.nome, t.cpf, t.rg
FROM acba_testemunhas t
LEFT JOIN acba_testemunhas_arrombamento ta ON ta.testemunha_id = t.id
WHERE t.tipo = 'arrombamento' AND ta.testemunha_id IS NULL;


-- Qualificação do morador presente em acba_records.
-- Aparece no formulário apenas quando morador_ausente_245_4 = FALSE.
-- (Validação de obrigatoriedade fica na camada de aplicação.)
ALTER TABLE acba_records
    ADD COLUMN morador_nome      VARCHAR(180) NOT NULL DEFAULT '',
    ADD COLUMN morador_cpf       VARCHAR(20)  NOT NULL DEFAULT '',
    ADD COLUMN morador_rg        VARCHAR(40)  NOT NULL DEFAULT '',
    ADD COLUMN morador_filiacao  VARCHAR(220) NOT NULL DEFAULT '',
    ADD COLUMN morador_telefone  VARCHAR(40)  NOT NULL DEFAULT '';


-- Migra os dados existentes do JSONB para a tabela nova. Os campos
-- introduzidos (cpf/rg/filiacao/endereco) recebem 'Não informado' como
-- placeholder; documento histórico vai para CPF e contato para telefone.
INSERT INTO acba_testemunhas
    (acba_id, nome, cpf, rg, filiacao, endereco, telefone, tipo, ordem)
SELECT a.id,
       COALESCE(NULLIF(trim(t->>'nome'),      ''), 'Não informado'),
       COALESCE(NULLIF(trim(t->>'documento'), ''), 'Não informado'),
       'Não informado',
       'Não informado',
       'Não informado',
       NULLIF(trim(t->>'contato'), ''),
       'geral',
       (arr.ord - 1)::int
FROM acba_records a
CROSS JOIN LATERAL jsonb_array_elements(a.testemunhas)
    WITH ORDINALITY AS arr(t, ord)
WHERE jsonb_typeof(a.testemunhas) = 'array';

ALTER TABLE acba_records DROP COLUMN testemunhas;
