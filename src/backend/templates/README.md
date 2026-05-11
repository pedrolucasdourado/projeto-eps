# Template DOCX do ACBA

A partir da V8 (materiais com especialização de informática), o serviço de geração de PDF
usa **docxtpl** — sintaxe Jinja dentro do `.docx` — para popular as duas tabelas de
material apreendido com loop, em vez do `python-docx` puro.

## 1. Coloque o `.docx` oficial em `acba_template.docx`

Renomeie o arquivo oficial **“A C B A - Auto Circunstanciado de Busca e Arrecadação.docx”** para
`acba_template.docx` ou configure `ACBA_DOCX_TEMPLATE_PATH` no `.env`.

## 2. Substitua os campos fixos pelos marcadores `{{...}}`

| Marcador | Conteúdo |
|----------|-----------|
| `{{ processo_numero }}` | Número do processo |
| `{{ protocolo_numero }}` | Número do protocolo (Prot.) |
| `{{ processo_descricao }}` | Descrição do processo (opcional) |
| `{{ unidade }}` | Unidade responsável |
| `{{ delegacia }}` | Delegacia |
| `{{ cidade }}` | Cidade |
| `{{ uf_sigla }}` | Sigla da UF |
| `{{ uf_nome }}` | Nome da UF |
| `{{ data_lavratura }}` | Data (dd/mm/aaaa) |
| `{{ hora_lavratura }}` | Hora (hh:mm) |
| `{{ delegado }}` | Autoridade policial / delegado |
| `{{ delegado_matricula }}` | Matrícula do delegado |
| `{{ escrivao }}` | Escrivão |
| `{{ tipo_procedimento }}` | Tipo de procedimento |
| `{{ procedimento_numero }}` | Número do procedimento |
| `{{ fundamento_legal }}` | Fundamento legal |
| `{{ endereco_busca }}` | Endereço |
| `{{ alvo_busca }}` | Alvo |
| `{{ nome_vara_criminal }}` | Vara criminal competente (ou `—`) |
| `{{ nome_juiz }}` | Nome do(a) juiz(a) que expediu o mandado (ou `—`) |
| `{{ equipe_numero }}` | Número da equipe |
| `{{ equipe_nome }}` | Nome da equipe |
| `{{ equipe_texto }}` | Texto multilinhas com cada agente |
| `{{ testemunhas_texto }}` | Texto multilinhas com cada testemunha (já inclui a qualificação quando for testemunha de arrombamento) |
| `{{ observacoes }}` | Observações |
| `{{ assinatura_responsavel }}` | Nome na linha de assinatura |

### Testemunhas em tabelas próprias

Duas listas pré-segregadas são expostas para permitir tabelas separadas no
modelo oficial:

| Marcador | Conteúdo |
|----------|-----------|
| `{{ testemunhas_gerais }}` | Testemunhas comuns. Cada item: `nome`, `cpf`, `rg`, `filiacao`, `endereco`, `cidade`, `telefone` |
| `{{ testemunhas_arrombamento }}` | Testemunhas vizinhas (Art. 245 §4º). Cada item: `nome`, `cpf`, `rg`, `filiacao`, `endereco`, `observacoes` |

Exemplos de uso (tabelas com `{%tr ... %}` do docxtpl):

```
{%tr for t in testemunhas_gerais %}
{{ t.nome }} (CPF {{ t.cpf }} / RG {{ t.rg }})
Filiação: {{ t.filiacao }} — Cidade: {{ t.cidade }} — Telefone: {{ t.telefone }}
Endereço: {{ t.endereco }}
{%tr endfor %}

{%tr for t in testemunhas_arrombamento %}
{{ t.nome }} (CPF {{ t.cpf }} / RG {{ t.rg }})
Filiação: {{ t.filiacao }}
Endereço: {{ t.endereco }}
Observações: {{ t.observacoes }}
{%tr endfor %}
```

### Morador presente (Art. 245 caput e §1º do CPP)

Quando o morador NÃO estava ausente (`morador_ausente_245_4 == False`), o
template tem disponíveis os seguintes marcadores:

| Marcador | Conteúdo |
|----------|-----------|
| `{{ morador_presente }}` | Boolean — `True` quando o morador foi qualificado |
| `{{ morador_nome }}` | Nome do morador (ou `—` quando ausente) |
| `{{ morador_cpf }}` | CPF do morador |
| `{{ morador_rg }}` | RG do morador |
| `{{ morador_filiacao }}` | Filiação do morador |
| `{{ morador_telefone }}` | Telefone do morador |

Bloco condicional típico:

```
{% if morador_presente %}
MORADOR: {{ morador_nome }} — CPF: {{ morador_cpf }} — RG: {{ morador_rg }}
Filiação: {{ morador_filiacao }} — Telefone: {{ morador_telefone }}
{% endif %}
```

### Bloco do Art. 245 §§ 2º, 3º e 4º do CPP

Para cada hipótese o operador marca uma caixa de seleção e pode preencher
um campo de observações. As variáveis booleanas (`True`/`False`) devem ser
renderizadas com `{% if ... %}Sim{% else %}Não{% endif %}` no template.

| Marcador | Conteúdo |
|----------|-----------|
| `{{ arrombamento_245_2 }}` | Boolean — houve arrombamento de porta / entrada forçada por desobediência do morador (§2º) |
| `{{ arrombamento_245_2_obs }}` | Observações livres do §2º (ou `—`) |
| `{{ forca_coisas_245_3 }}` | Boolean — houve emprego de força contra coisas no interior da casa por recalcitrância do morador (§3º) |
| `{{ forca_coisas_245_3_obs }}` | Observações livres do §3º (ou `—`) |
| `{{ morador_ausente_245_4 }}` | Boolean — morador ausente; foi necessário arrombamento + emprego de força (§4º) |
| `{{ morador_ausente_245_4_obs }}` | Observações livres do §4º (ou `—`) |

## 3. Tabelas dinâmicas com loop (materiais)

Use a sintaxe especial `{%tr ... %}` do docxtpl **dentro da linha-modelo da tabela**, para
repetir a linha por item. Existem duas tabelas (corresponde ao que o auto oficial já tem):

### Tabela de material de **informática** (com coluna SENHA)

Linha-modelo deve conter, em cada célula, respectivamente:

```
{%tr for m in materiais_informatica %}
{{ m.item_num }}
{{ m.descricao }}{% if m.localizacao %} — Local: {{ m.localizacao }}{% endif %}
{{ m.senha_render }}
{%tr endfor %}
```

A célula `senha_render` recebe automaticamente:
- a senha em texto (quando o operador escolheu `senha_tipo='texto'`);
- uma **imagem PNG do padrão de bloqueio** com setas e ponto inicial destacado
  (quando `senha_tipo='padrao'`), gerada em tempo de exportação;
- "Biometria — observação", "Desconhecida", ou "—" nos demais casos.

### Tabela de material **geral** (sem coluna SENHA)

```
{%tr for m in materiais_geral %}
{{ m.item_num }}
{{ m.descricao }}{% if m.localizacao %} — Local: {{ m.localizacao }}{% endif %}
{%tr endfor %}
```

## 4. Geração de template stub para desenvolvimento

```bash
cd src/backend && pip install -r requirements.txt && python scripts/generate_acba_template_docx.py
```

O backend preenche o template e converte para PDF com **LibreOffice** no container.
