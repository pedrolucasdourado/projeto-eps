# Template DOCX do ACBA

1. Coloque aqui o arquivo oficial **“A C B A - Auto Circunstanciado de Busca e Arrecadação (1).docx”** (renomeie para `acba_template.docx` ou configure `ACBA_DOCX_TEMPLATE_PATH`).
2. Insira nos pontos variáveis os seguintes marcadores de texto (um por campo), preservando o restante do layout:

| Marcador | Conteúdo |
|----------|-----------|
| `{{numero_auto}}` | Número do auto |
| `{{unidade}}` | Unidade responsável |
| `{{delegacia}}` | Delegacia |
| `{{cidade}}` | Cidade |
| `{{uf_sigla}}` | Sigla da UF |
| `{{uf_nome}}` | Nome da UF |
| `{{data_lavratura}}` | Data (dd/mm/aaaa) |
| `{{hora_lavratura}}` | Hora (hh:mm) |
| `{{autoridade}}` | Autoridade policial |
| `{{autoridade_matricula}}` | Matrícula da autoridade |
| `{{escrivao}}` | Escrivão |
| `{{tipo_procedimento}}` | Tipo de procedimento |
| `{{procedimento_numero}}` | Número do procedimento |
| `{{fundamento_legal}}` | Fundamento |
| `{{endereco_busca}}` | Endereço |
| `{{alvo_busca}}` | Alvo |
| `{{equipe_texto}}` | Equipe (bloco multilinhas) |
| `{{objetos_texto}}` | Objetos (bloco multilinhas) |
| `{{testemunhas_texto}}` | Testemunhas (bloco multilinhas) |
| `{{observacoes}}` | Observações |
| `{{condutor}}` | Condutor |
| `{{condutor_matricula}}` | Matrícula do condutor |
| `{{assinatura_responsavel}}` | Nome na linha de assinatura |

3. O backend preenche esses trechos e converte para PDF com **LibreOffice** no container.

Para gerar um modelo mínimo com todos os marcadores (desenvolvimento):

```bash
cd src/backend && pip install python-docx && python scripts/generate_acba_template_docx.py
```
