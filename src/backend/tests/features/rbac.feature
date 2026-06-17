# language: pt
Funcionalidade: Controle de acesso baseado em perfil (RBAC)

  Como sistema AAI
  Quero garantir que cada perfil só acesse o que lhe é permitido
  Para proteger dados sensíveis de operações policiais

  # --- Administrador ---

  Cenário: Administrador acessa gerenciamento de usuários
    Dado que estou autenticado como administrador
    Quando eu envio uma requisição GET para "/api/users/"
    Então o sistema retorna status 200

  Cenário: Administrador não acessa módulo ACBA
    Dado que estou autenticado como administrador
    Quando eu envio uma requisição GET para "/api/acba/"
    Então o sistema retorna status 403
    E o corpo da resposta menciona "Administradores"

  Cenário: Perfis não-administradores não acessam gerenciamento de usuários
    Dado que estou autenticado como delegado
    Quando eu envio uma requisição GET para "/api/users/"
    Então o sistema retorna status 403

  # --- Delegado ---

  Cenário: Delegado tem escopo irrestrito nos ACBAs
    Dado que estou autenticado como delegado
    Quando eu consulto a lista de ACBAs
    Então o sistema não aplica filtro por equipe

  Cenário: Delegado pode criar cadastros (UF, delegacia, equipe etc.)
    Dado que estou autenticado como delegado
    Quando eu envio uma requisição POST para "/api/cadastros/ufs" com payload válido
    Então o sistema retorna status 201 ou 200

  # --- Escrivão ---

  Cenário: Escrivão acessa apenas ACBAs de suas equipes
    Dado que estou autenticado como escrivão vinculado à equipe 5
    Quando eu envio uma requisição GET para "/api/acba/{id}" de ACBA da equipe 9
    Então o sistema retorna status 403

  Cenário: Escrivão não pode excluir ACBA
    Dado que estou autenticado como escrivão
    Quando eu envio uma requisição DELETE para "/api/acba/{id}"
    Então o sistema retorna status 403

  # --- Agente ---

  Cenário: Agente só visualiza ACBAs de equipes em que participou
    Dado que estou autenticado como agente que nunca esteve na equipe 7
    Quando eu envio uma requisição GET para "/api/acba/{id}" de ACBA da equipe 7
    Então o sistema retorna status 404

  Cenário: Agente vê ACBAs apenas dentro do seu período de vínculo
    Dado que estou autenticado como agente que esteve na equipe 3 de jan/2025 a mar/2025
    Quando eu consulto a lista de ACBAs
    Então apenas ACBAs com data_lavratura entre jan/2025 e mar/2025 da equipe 3 são retornados

  Cenário: Agente não pode criar ACBA
    Dado que estou autenticado como agente
    Quando eu envio uma requisição POST para "/api/acba/"
    Então o sistema retorna status 403

  Cenário: Agente não pode editar ACBA
    Dado que estou autenticado como agente
    Quando eu envio uma requisição PUT para "/api/acba/{id}"
    Então o sistema retorna status 403

  # --- Sem autenticação ---

  Cenário: Qualquer rota protegida rejeita requisição sem token
    Quando eu envio uma requisição GET para "/api/acba/" sem token de autenticação
    Então o sistema retorna status 401
