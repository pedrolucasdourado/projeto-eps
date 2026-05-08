-- Usuários do sistema (base para autenticação e expansão futura)
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name   VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users (email);

-- Credenciais de teste: admin@admin.com / admin123 (bcrypt)
INSERT INTO users (email, password_hash, full_name)
VALUES (
    'admin@admin.com',
    '$2b$12$Ho9gEOM6XwD1RmWkuHrXf.kj.Fp1fM/7IMfjUYxnfIsFm3MV9vvcG',
    'Administrador'
);
