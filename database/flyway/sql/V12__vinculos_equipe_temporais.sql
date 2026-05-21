-- V12: Histórico temporal de vínculos agente↔equipe.
--
-- Substitui equipe_operacional_membros (sem período) por
-- equipe_operacional_vinculos, em que cada linha representa UMA passagem
-- de um agente por uma equipe, com data de início obrigatória e data de
-- fim opcional (NULL = vínculo ainda ativo).
--
-- Por que?
--   * Quando um agente sai da equipe, ele continua precisando enxergar
--     os ACBAs do tempo em que estava lá (e SOMENTE desse período).
--   * Um mesmo agente pode entrar e sair da mesma equipe mais de uma vez,
--     e pode pertencer a várias equipes ao mesmo tempo.
--
-- Como o módulo ainda está em estágio inicial, a migração é destrutiva:
-- o schema novo é criado, o antigo é removido, e a V99 (seeds) repovoa
-- a nova tabela já no formato temporal. Nada a preservar em produção.

CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE equipe_operacional_vinculos (
    id           SERIAL PRIMARY KEY,
    equipe_id    INTEGER NOT NULL REFERENCES equipes_operacionais(id) ON DELETE CASCADE,
    agente_id    INTEGER NOT NULL REFERENCES agentes(id) ON DELETE CASCADE,
    data_inicio  DATE    NOT NULL,
    data_fim     DATE,
    motivo_saida VARCHAR(160),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_vinc_periodo
        CHECK (data_fim IS NULL OR data_fim >= data_inicio),
    -- Impede que um mesmo agente tenha dois períodos sobrepostos na MESMA
    -- equipe. Períodos abertos são tratados como indo até DATE 'infinity'.
    CONSTRAINT uq_vinc_sem_overlap EXCLUDE USING gist (
        equipe_id WITH =,
        agente_id WITH =,
        daterange(
            data_inicio,
            COALESCE(data_fim, DATE 'infinity'),
            '[]'
        ) WITH &&
    )
);

CREATE INDEX idx_vinc_agente_periodo
    ON equipe_operacional_vinculos (agente_id, data_inicio, data_fim);

CREATE INDEX idx_vinc_equipe_periodo
    ON equipe_operacional_vinculos (equipe_id, data_inicio, data_fim);

-- Acesso rápido a "vínculos abertos hoje" — usado por listas de membros
-- atuais e pelo CRUD de equipes (que mostra/edita só quem está vigente).
CREATE INDEX idx_vinc_ativos
    ON equipe_operacional_vinculos (equipe_id, agente_id)
    WHERE data_fim IS NULL;

DROP TABLE equipe_operacional_membros;
