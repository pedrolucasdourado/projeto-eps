[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/5NN1Yng5)
# template-fcte-unb-eps5
# 🛡️ FCTE-UNB-EPS5: Operação Base PCDF (SecOps-First)

Este repositório é a matriz oficial para o desenvolvimento dos aplicativos em parceria com a PCDF. O foco é a **Paridade UnB-PCDF** e a aplicação do **Domínio 8 do CISSP** (Segurança no Desenvolvimento de Software).

## 🚀 Desafios por Squad (Contexto Operacional)

Cada grupo deve focar nos requisitos específicos de seu sistema, conforme o detalhamento técnico:

### 1. Sistema de Preservação e Coleta de Vestígios Digital - cadeia de custodia
* [cite_start]**Objetivo**: Garantir a Cadeia de Custódia (Lei nº 13.964/2019)[cite: 2].
* [cite_start]**Mandatório**: Geração de Hash SHA-256 imediata e trilha de auditoria (Audit Trail)[cite: 6, 8].
* [cite_start]**Segurança**: Armazenamento imutável (WORM/Blockchain) e criptografia AES-256[cite: 10, 12].

### 2. Assistente de Apreensão Inteligente (Computer Vision)
* [cite_start]**Objetivo**: Automatizar a lavratura do Auto de Apreensão via IA[cite: 56].
* [cite_start]**Mandatório**: OCR para extração de números de série/IMEI e classificação de objetos (Armas, Celulares)[cite: 58].
* [cite_start]**Segurança**: Privacidade (LGPD) com desfoque automático de rostos de terceiros[cite: 61].

### 3. Buscador OSINT Automatizado
* [cite_start]**Objetivo**: Reduzir o tempo de levantamento de dados em fontes abertas[cite: 35].
* [cite_start]**Mandatório**: Busca Federada (CPF, Nome, Vulgo) e captura de evidências (Snapshots)[cite: 36, 38].
* [cite_start]**Segurança**: Anonimato operacional com rotação de IP e VPN para mascarar a origem PCDF[cite: 41, 51].

### 4. Analisador Semântico de Documentos
* [cite_start]**Objetivo**: Automatizar a triagem de depoimentos e documentos via NLP/LLM[cite: 73].
* [cite_start]**Mandatório**: Extração de entidades (NER), análise de contradições e geração de cronologia[cite: 76, 77].
* [cite_start]**Segurança**: Baixa alucinação via RAG e processamento em modelos locais (Local-LLM) para privacidade total[cite: 79].

---

## 🛠️ Setup do Ambiente (DevSecOps)

Para garantir a validade jurídica, o ambiente deve ser isolado:

1. [cite_start]**Docker**: Execute `docker-compose up --build` para subir o app e o banco PostgreSQL[cite: 31, 67].
2. [cite_start]**Auditoria**: O pipeline de CI/CD rodará automaticamente o **Bandit** (SAST) e o **Safety** (SCA).
3. **Validação**: Utilize o script `src/olaseguranca.py` para testar a validação de dados com Pydantic.

## 📝 Diário de Bordo (Esforço Documentado)
Registre aqui os erros de infraestrutura encontrados durante o mês de março:

| Data | Componente | Erro Identificado | Solução |
| :--- | :--- | :--- | :--- |
| | | | |
