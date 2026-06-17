# language: pt
Funcionalidade: Autenticação de usuário

  Como um usuário do sistema AAI
  Quero me autenticar com e-mail e senha
  Para acessar as funcionalidades do meu perfil

  Cenário: Login com credenciais válidas retorna token
    Dado que existe um usuário com e-mail "delegado@pcdf.gov.br" e senha "Senha@123"
    Quando eu envio uma requisição POST para "/api/auth/login" com as credenciais
    Então o sistema retorna status 200
    E o corpo da resposta contém um "access_token"
    E o campo "token_type" é "bearer"
    E o campo "user.role" é "delegado"

  Cenário: Login com e-mail inexistente é rejeitado
    Dado que não existe usuário com e-mail "fantasma@pcdf.gov.br"
    Quando eu envio uma requisição POST para "/api/auth/login" com esse e-mail
    Então o sistema retorna status 401
    E o corpo da resposta contém o detalhe "E-mail ou senha inválidos."

  Cenário: Login com senha incorreta é rejeitado
    Dado que existe um usuário com e-mail "delegado@pcdf.gov.br"
    Quando eu envio login com a senha "SenhaErrada"
    Então o sistema retorna status 401
    E o corpo da resposta contém o detalhe "E-mail ou senha inválidos."

  Cenário: Login com usuário desativado é rejeitado
    Dado que existe um usuário com e-mail "inativo@pcdf.gov.br" e situação "desativado"
    Quando eu envio login com as credenciais corretas
    Então o sistema retorna status 401

  Cenário: Consulta de perfil exige autenticação
    Quando eu envio uma requisição GET para "/api/auth/me" sem token
    Então o sistema retorna status 401

  Cenário: Consulta de perfil com token válido retorna dados do usuário
    Dado que estou autenticado como "escrivao@pcdf.gov.br"
    Quando eu envio uma requisição GET para "/api/auth/me" com o token
    Então o sistema retorna status 200
    E o campo "role" é "escrivao"
