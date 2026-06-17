# language: pt
Funcionalidade: Gerenciamento de ACBA

  Como delegado ou escrivão da PCDF
  Quero criar, consultar e editar ACBAs
  Para registrar e gerir autos de busca e apreensão

  Cenário: Delegado cria ACBA com dados válidos
    Dado que estou autenticado como delegado da equipe 1
    Quando eu envio uma requisição POST para "/api/acba/" com payload válido
    Então o sistema retorna status 201
    E o corpo da resposta contém um campo "id"
    E o campo "protocolo_numero" corresponde ao informado

  Cenário: Agente não pode criar ACBA
    Dado que estou autenticado como agente da equipe 1
    Quando eu envio uma requisição POST para "/api/acba/" com payload válido
    Então o sistema retorna status 403

  Cenário: Escrivão visualiza apenas ACBAs da sua equipe
    Dado que estou autenticado como escrivão da equipe 2
    E existem ACBAs das equipes 1 e 2
    Quando eu envio uma requisição GET para "/api/acba/"
    Então o sistema retorna status 200
    E todos os ACBAs retornados pertencem à equipe 2

  Cenário: Delegado visualiza todos os ACBAs
    Dado que estou autenticado como delegado
    E existem ACBAs das equipes 1, 2 e 3
    Quando eu envio uma requisição GET para "/api/acba/"
    Então o sistema retorna status 200
    E ACBAs de todas as equipes estão presentes

  Cenário: Edição de ACBA é bloqueada após geração do PDF para escrivão
    Dado que estou autenticado como escrivão da equipe 1
    E existe um ACBA da equipe 1 com PDF já gerado
    Quando eu envio uma requisição PUT para "/api/acba/{id}" com dados alterados
    Então o sistema retorna status 409
    E o corpo da resposta menciona "PDF"

  Cenário: Delegado pode editar ACBA mesmo após geração do PDF
    Dado que estou autenticado como delegado
    E existe um ACBA com PDF já gerado
    Quando eu envio uma requisição PUT para "/api/acba/{id}" com dados alterados
    Então o sistema retorna status 200

  Cenário: Apenas delegado pode excluir ACBA
    Dado que estou autenticado como escrivão
    Quando eu envio uma requisição DELETE para "/api/acba/{id}"
    Então o sistema retorna status 403
