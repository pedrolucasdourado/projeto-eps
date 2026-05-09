-- V6: renomear tabelas para os cadastros de policiais (agentes, delegados),
-- mover delegado/escrivão para a equipe como vínculos obrigatórios,
-- remover condutores e os campos derivados do ACBA.

-- 1. Renomear cadastros
ALTER TABLE membros_equipe_operacional RENAME TO agentes;
ALTER TABLE autoridades_policiais RENAME TO delegados;

-- 2. Renomear coluna da link table para refletir o novo nome
ALTER TABLE equipe_operacional_membros RENAME COLUMN membro_id TO agente_id;

-- 3. Renomear índices/constraints para manter consistência (não obrigatório, mas ajuda)
ALTER INDEX idx_equipe_op_membros_membro RENAME TO idx_equipe_op_agentes_agente;
ALTER INDEX idx_autoridades_delegacia RENAME TO idx_delegados_delegacia;
ALTER INDEX idx_autoridades_unidade RENAME TO idx_delegados_unidade;

-- 4. Acrescentar delegado_id e escrivao_id na equipe (nullable enquanto migra)
ALTER TABLE equipes_operacionais
    ADD COLUMN delegado_id INTEGER REFERENCES delegados(id),
    ADD COLUMN escrivao_id INTEGER REFERENCES escrivaos(id);

-- 5. Derivar delegado/escrivão de cada equipe a partir do ACBA mais recente
--    que a referencia. ACBAs antigos compartilhando a mesma equipe vão herdar
--    a mesma autoridade/escrivão; isto pode ser ajustado manualmente depois.
UPDATE equipes_operacionais eq
SET delegado_id = sub.autoridade_id,
    escrivao_id = sub.escrivao_id
FROM (
    SELECT DISTINCT ON (a.equipe_id)
           a.equipe_id, a.autoridade_id, a.escrivao_id
    FROM acba_records a
    ORDER BY a.equipe_id, a.created_at DESC
) sub
WHERE eq.id = sub.equipe_id;

-- 6. Remover equipes placeholder (sem uso) — caso de '0' Sem equipe criada por V5
DELETE FROM equipes_operacionais e
WHERE e.delegado_id IS NULL
  AND e.escrivao_id IS NULL
  AND NOT EXISTS (SELECT 1 FROM acba_records a WHERE a.equipe_id = e.id)
  AND NOT EXISTS (SELECT 1 FROM equipe_operacional_membros em WHERE em.equipe_id = e.id);

-- 7. Drop colunas do ACBA que agora são derivadas da equipe
ALTER TABLE acba_records
    DROP COLUMN autoridade_id,
    DROP COLUMN escrivao_id,
    DROP COLUMN condutor_id;

-- 8. Remover cadastro de condutores
DROP TABLE condutores_operacao;

-- 9. Tornar delegado/escrivão obrigatórios na equipe
ALTER TABLE equipes_operacionais
    ALTER COLUMN delegado_id SET NOT NULL,
    ALTER COLUMN escrivao_id SET NOT NULL;

CREATE INDEX idx_equipes_delegado ON equipes_operacionais (delegado_id);
CREATE INDEX idx_equipes_escrivao ON equipes_operacionais (escrivao_id);
