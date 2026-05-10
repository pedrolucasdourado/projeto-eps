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
| `{{ equipe_numero }}` | Número da equipe |
| `{{ equipe_nome }}` | Nome da equipe |
| `{{ equipe_texto }}` | Texto multilinhas com cada agente |
| `{{ testemunhas_texto }}` | Texto multilinhas com cada testemunha |
| `{{ observacoes }}` | Observações |
| `{{ assinatura_responsavel }}` | Nome na linha de assinatura |

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
