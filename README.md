# Extrator de Dados de PDF com IA

Transforma PDFs não estruturados (aqui, **notas fiscais de serviço**) em **JSON e Excel validados**, usando um LLM para a leitura e **Pydantic** para garantir que a saída está correta antes de seguir para o próximo sistema.

> Projeto de portfólio inspirado em automações de leitura de documentos com IA que desenvolvi profissionalmente. Código escrito do zero, com documentos 100% fictícios.

## O problema

Equipes de backoffice recebem centenas de PDFs (notas fiscais, comprovantes, documentos de cadastro) e digitam manualmente os dados no ERP. Regex sozinho quebra a cada layout novo; IA sozinha às vezes "inventa" um valor. A solução combina os dois mundos: **a IA lê, o código valida**.

## Como funciona

```
PDF ──► PyMuPDF (texto) ──► Provedor de IA ──► JSON ──► Pydantic ──► resultado.json / resultado.xlsx
            │                     ▲                         │
            └─ sem texto? ─► status "sem_texto"             └─ inválido? reenvia o erro para a IA (1 nova tentativa)
```

- **Esquema como contrato**: o JSON Schema do modelo Pydantic vai no prompt, e a resposta é validada contra ele
- **Regras de negócio na validação**: CNPJ normalizado, valor > 0 e `valor_liquido = valor_servicos − retenções`
- **Autocorreção**: se a validação falha, a mensagem de erro volta para a IA, que corrige na segunda tentativa
- **Provedores plugáveis**: `claude` (API da Anthropic) ou `regex` (offline, para demo e testes). Para outro fornecedor, basta implementar `Provedor.extrair`
- **Status por arquivo**: `sucesso`, `sem_texto` (precisa de OCR), `falha_validacao`, `erro`, o que facilita a fila de exceções para um humano revisar

## Executando

```bash
pip install -r requirements.txt
python scripts/gerar_exemplos.py                 # NFS-e fictícias em exemplos/

# Offline (sem chave de API)
python -m extrator_ia exemplos --provedor regex

# Com IA
cp .env.example .env    # preencha ANTHROPIC_API_KEY
python -m extrator_ia exemplos --provedor claude
```

Saída: `output/resultado.json` e `output/resultado.xlsx` (uma linha por documento, campos aninhados achatados).

```
2/4 documento(s) extraído(s) com sucesso → output/
```

Nos exemplos, uma nota tem o valor líquido propositalmente errado e outra é um PDF escaneado. Os dois casos são detectados e não seguem adiante.

## Estrutura

```
extrator_ia/
├── schemas.py      # modelos Pydantic (contrato de saída + regras de validação)
├── provedores.py   # ClaudeProvider, RegexProvider e a interface Provedor
├── pipeline.py     # orquestração, novas tentativas e status
└── __main__.py     # CLI + exportação JSON/Excel
```

## Testes

```bash
pytest
```

Incluem um provedor falso que erra na primeira resposta, para provar que o feedback de validação é reenviado e corrigido.

## Segurança e privacidade

- Chaves ficam só no `.env` (fora do Git); o `.env.example` documenta as variáveis
- Para documentos com dados pessoais reais, avalie a LGPD: base legal, minimização (envie só as páginas necessárias) e a política de retenção do fornecedor de IA

## Tecnologias

Python 3.10+ · Anthropic API · Pydantic v2 · PyMuPDF · pandas · pytest

---
Desenvolvido por **Yasmim Santos** · Licença MIT
