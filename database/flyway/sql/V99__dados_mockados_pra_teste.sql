-- Credenciais de teste: admin@admin.com / admin123 (bcrypt)
INSERT INTO users (email, password_hash, full_name)
VALUES (
    'admin@admin.com',
    '$2b$12$Ho9gEOM6XwD1RmWkuHrXf.kj.Fp1fM/7IMfjUYxnfIsFm3MV9vvcG',
    'Administrador'
);

-- UF + cidade
INSERT INTO ufs (sigla, nome) VALUES ('DF', 'Distrito Federal');

INSERT INTO cidades (nome, uf_id)
SELECT 'Brasília', id FROM ufs WHERE sigla = 'DF';

-- Tipos de procedimento
INSERT INTO tipos_procedimento (nome) VALUES
    ('Inquérito Policial'),
    ('Termo Circunstanciado');

-- Unidades responsáveis
INSERT INTO unidades_responsaveis (nome) VALUES
    ('Departamento de Polícia da Capital — DPC'),
    ('Departamento de Polícia Especializada — DPE');

-- Delegacias
INSERT INTO delegacias (nome, unidade_id, cidade_id)
SELECT '1ª Delegacia de Polícia', u.id, c.id
FROM unidades_responsaveis u, cidades c
WHERE u.nome = 'Departamento de Polícia da Capital — DPC'
  AND c.nome = 'Brasília';

INSERT INTO delegacias (nome, unidade_id, cidade_id)
SELECT 'Delegacia Especial de Repressão a Entorpecentes — DRE',
       u.id, c.id
FROM unidades_responsaveis u, cidades c
WHERE u.nome = 'Departamento de Polícia Especializada — DPE'
  AND c.nome = 'Brasília';

-- Delegados (autoridade policial)
INSERT INTO delegados (nome, matricula, delegacia_id, unidade_id)
SELECT 'Dr. Carlos Andrade', '12345-X', d.id, d.unidade_id
FROM delegacias d WHERE d.nome = '1ª Delegacia de Polícia';

INSERT INTO delegados (nome, matricula, delegacia_id, unidade_id)
SELECT 'Dra. Marina Souza', '54321-Y', d.id, d.unidade_id
FROM delegacias d
WHERE d.nome = 'Delegacia Especial de Repressão a Entorpecentes — DRE';

-- Escrivãos
INSERT INTO escrivaos (nome, delegacia_id, unidade_id)
SELECT 'Pedro Oliveira', d.id, d.unidade_id
FROM delegacias d WHERE d.nome = '1ª Delegacia de Polícia';

INSERT INTO escrivaos (nome, delegacia_id, unidade_id)
SELECT 'Ana Lima', d.id, d.unidade_id
FROM delegacias d
WHERE d.nome = 'Delegacia Especial de Repressão a Entorpecentes — DRE';

-- Agentes (cadastro de policiais operacionais)
INSERT INTO agentes (nome, matricula, funcao_padrao) VALUES
    ('Roberto Silva',     'A-1001', 'Agente'),
    ('Juliana Costa',     'A-1002', 'Agente'),
    ('Felipe Rocha',      'A-1003', 'Investigador'),
    ('Patrícia Mendes',   'A-1004', 'Investigador'),
    ('Lucas Fernandes',   'A-1005', 'Papiloscopista'),
    ('Renata Alves',      'A-1006', 'Agente');

-- Equipes operacionais (delegado + escrivão obrigatórios)
INSERT INTO equipes_operacionais (numero, nome, delegado_id, escrivao_id)
SELECT '01', 'Equipe Tático Alfa',
       (SELECT id FROM delegados WHERE matricula = '12345-X'),
       (SELECT id FROM escrivaos WHERE nome = 'Pedro Oliveira');

INSERT INTO equipes_operacionais (numero, nome, delegado_id, escrivao_id)
SELECT '02', 'Equipe Antientorpecentes',
       (SELECT id FROM delegados WHERE matricula = '54321-Y'),
       (SELECT id FROM escrivaos WHERE nome = 'Ana Lima');

-- Vínculo agentes ↔ equipes (um agente pode estar em mais de uma equipe)
INSERT INTO equipe_operacional_membros (equipe_id, agente_id)
SELECT eq.id, a.id
FROM equipes_operacionais eq
JOIN agentes a ON a.matricula IN ('A-1001', 'A-1002', 'A-1003')
WHERE eq.numero = '01';

INSERT INTO equipe_operacional_membros (equipe_id, agente_id)
SELECT eq.id, a.id
FROM equipes_operacionais eq
JOIN agentes a ON a.matricula IN ('A-1004', 'A-1005', 'A-1006', 'A-1001')
WHERE eq.numero = '02';

-- Processos de exemplo. Cada ACBA escolhe um processo e informa o protocolo
-- daquela diligência diretamente no formulário (o protocolo não tem cadastro).
INSERT INTO processos (numero, descricao) VALUES
    ('0001234-56.2025.8.07.0001', 'Operação Aurora — investigação de organização criminosa'),
    ('0007890-12.2025.8.07.0002', 'Operação Farol — entorpecentes e lavagem de capitais');
