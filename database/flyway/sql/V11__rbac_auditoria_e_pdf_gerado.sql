-- V11: Controle de acesso por papel (RBAC), vínculo login ↔ cadastro real,
-- marcação de PDF gerado e tabela de auditoria do ACBA.
--
-- Modelagem:
--   * users.role         - 4 papéis: administrador, delegado, escrivao, agente.
--                          Cada usuário tem exatamente UM papel.
--   * users.ativo        - permite desativar acesso sem apagar o histórico.
--   * delegados/escrivaos/agentes.user_id (UNIQUE, NULL permitido)
--                          - vincula um cadastro real ao login que opera por ele.
--                            Garante 1↔1 e permite excluir o usuário sem perder
--                            a referência histórica do cadastro.
--   * acba_records.pdf_gerado_at + pdf_gerado_por_user_id
--                          - bloqueio do escrivão é disparado por estas colunas
--                            estarem preenchidas; o delegado segue podendo editar.
--   * acba_audit_log     - histórico imutável de alterações do ACBA. Cada linha
--                          guarda quem alterou, papel naquele momento, ação,
--                          snapshot ANTES da alteração (suporta "ver versão
--                          anterior") e snapshot DEPOIS, mais um diff calculado
--                          pela aplicação, IP e user-agent.
--
-- Estratégia conservadora: tudo aditivo, sem renomear colunas existentes.

-- 1. Papel e flag de ativo nos usuários.
ALTER TABLE users
    ADD COLUMN role        VARCHAR(20) NOT NULL DEFAULT 'administrador',
    ADD COLUMN ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    ADD CONSTRAINT users_role_check
        CHECK (role IN ('administrador','delegado','escrivao','agente'));

CREATE INDEX idx_users_role ON users (role);
CREATE INDEX idx_users_ativo ON users (ativo);

-- 2. Garante que o seed admin@admin.com siga como administrador (defensivo;
--    o default já cuida do caso comum, mas deixamos explícito).
UPDATE users SET role = 'administrador'
WHERE LOWER(email) = 'admin@admin.com';

-- 3. Vínculo cadastro ↔ login. UNIQUE para forçar 1↔1; NULL permitido enquanto
--    o cadastro não tem login associado (caso comum no seed).
ALTER TABLE delegados
    ADD COLUMN user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE escrivaos
    ADD COLUMN user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE agentes
    ADD COLUMN user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX idx_delegados_user ON delegados (user_id);
CREATE INDEX idx_escrivaos_user ON escrivaos (user_id);
CREATE INDEX idx_agentes_user   ON agentes (user_id);

-- 4. Marcação de PDF gerado no ACBA.
ALTER TABLE acba_records
    ADD COLUMN pdf_gerado_at         TIMESTAMPTZ,
    ADD COLUMN pdf_gerado_por_user_id INTEGER REFERENCES users(id);

CREATE INDEX idx_acba_pdf_gerado ON acba_records (pdf_gerado_at)
    WHERE pdf_gerado_at IS NOT NULL;

-- 5. Auditoria.
CREATE TABLE acba_audit_log (
    id                  SERIAL PRIMARY KEY,
    acba_id             INTEGER NOT NULL REFERENCES acba_records(id),
    user_id             INTEGER REFERENCES users(id),
    user_email          VARCHAR(255) NOT NULL,
    user_full_name      VARCHAR(255),
    user_role           VARCHAR(20) NOT NULL,
    acao                VARCHAR(30) NOT NULL
        CHECK (acao IN ('criado','editado','excluido','pdf_gerado')),
    changed_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    snapshot_before     JSONB,
    snapshot_after      JSONB,
    changes             JSONB,
    ip                  VARCHAR(64),
    user_agent          TEXT
);

CREATE INDEX idx_audit_acba       ON acba_audit_log (acba_id);
CREATE INDEX idx_audit_changed_at ON acba_audit_log (changed_at DESC);
CREATE INDEX idx_audit_user       ON acba_audit_log (user_id);
CREATE INDEX idx_audit_acao       ON acba_audit_log (acao);
