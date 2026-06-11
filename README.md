# Agente de Triagem de E-mails — AgentOS / Agno

Agente semi-autônomo (nível 2) que faz a triagem de e-mails operacionais:
classifica prioridade, identifica o setor responsável, sugere uma resposta para
revisão humana e sinaliza casos que devem ser escalados.

Projeto da disciplina (Aula 08 — Agno, AgentOS, ferramentas customizadas, memória
e tracing).

---

## 1. Requisitos

- Python 3.10 ou superior
- Conta na OpenAI (chave de API) — ou Groq, opcional
- Conta no [os.agno.com](https://os.agno.com) para testar via Studio (modo Local)

## 2. Instalação

```bash
# 1) Clone ou copie esta pasta
cd meu_agente

# 2) Crie e ative um ambiente virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/Mac:
# source .venv/bin/activate

# 3) Instale as dependências
pip install -r requirements.txt

# 4) Configure as variáveis de ambiente
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac
# Abra o arquivo .env e cole sua OPENAI_API_KEY
```

## 3. Execução

```bash
fastapi dev agente.py
```

A API sobe em `http://localhost:8000`. Endpoints úteis:

- `GET  /ui`                — **interface web local** (inserir e-mail e ver a triagem)
- `GET  /health`            — health check
- `POST /agents/.../runs`   — endpoint do agente
- `GET  /docs`              — Swagger UI (gerado pelo FastAPI)

### Interface web local

Além do Studio, o projeto inclui uma interface própria em
**`http://127.0.0.1:8000/ui`** ([interface.py](interface.py)) — cumpre o papel
do Streamlit previsto no mapeamento da Aula 08: campo para colar o e-mail,
triagem com um clique e destaque visual em vermelho para casos que exigem
revisão humana (`[ESCALAR PARA HUMANO]`). Não requer dependências extras:
a página é servida pelo próprio FastAPI do AgentOS e consome o endpoint REST
`/agents/agente-de-triagem-de-e-mails/runs`.

## 4. Testando via Studio

1. Acesse [https://os.agno.com](https://os.agno.com).
2. Clique em **Connect AgentOS** e escolha o modo **Local**.
3. Aponte para **`http://127.0.0.1:8000`** (use `127.0.0.1`, **não** `localhost` — veja a nota de IPv6 abaixo).
4. Selecione o agente **Agente de Triagem de E-mails** e clique em **REFRESH**.

> ⚠️ **No Windows, use `127.0.0.1:8000` em vez de `localhost:8000`.** Em muitas máquinas Windows o `localhost` resolve para IPv6 (`::1`), mas o servidor escuta em IPv4 (`127.0.0.1`). Isso faz o navegador mostrar "Failed to connect to the AgentOS" mesmo com o servidor no ar. Usar `127.0.0.1` força IPv4 e resolve.

### Roteiro mínimo de testes (5 conversas)

1. **Ferramenta 1 + 2 + 3 (caso simples)** — `user_id: adrian`
   > "Triagem deste e-mail: 'Bom dia, gostaria de saber o status do meu boleto vencido ontem.'"
2. **Ferramenta 4 + escalação humana**
   > "Triagem: 'Vou abrir reclamação no Procon, isso é fraude, exijo cancelamento imediato do contrato.'"
3. **Alimentar memória** — mesma sessão
   > "Para sua informação: meu nome é Ana e atuo no setor financeiro."
4. **Nova sessão, mesmo `user_id`** — recuperar memória
   > "Você lembra quem eu sou e em que setor trabalho?"
5. **Caso ambíguo** (continuidade / `add_history_to_context`)
   > "E se esse mesmo e-mail viesse de um cliente novo, mudaria sua classificação?"

Capturar prints das abas **Chat**, **Sessions**, **Memories** e **Traces** do Studio.

## 5. Estrutura

```
meu_agente/
├── .env              # NÃO commitar — contém a chave da API
├── .env.example      # template
├── .gitignore
├── requirements.txt
├── README.md         # este arquivo
├── agente.py         # AgentOS principal (Agent + AgentOS + FastAPI)
├── ferramentas.py    # 4 tools customizadas
└── relatorio.md      # Etapa 5 do trabalho
```

## 6. Trocar para Groq (opcional)

No `agente.py`, troque:

```python
from agno.models.openai import OpenAIChat
...
model=OpenAIChat(id="gpt-4o-mini"),
```

por:

```python
from agno.models.groq import Groq
...
model=Groq(id="llama-3.3-70b-versatile"),
```

E configure `GROQ_API_KEY` no `.env`.

## 7. Solução de problemas

- **`ModuleNotFoundError: agno`** — confirme que o venv está ativo e rode `pip install -r requirements.txt` novamente.
- **`Invalid API key` / `Incorrect API key provided`** — verifique se o `.env` está na raiz, sem espaços nem aspas, e que a chave começa com `sk-`. Confirme também que a conta OpenAI tem créditos/billing ativo.
- **Studio mostra "Failed to connect to the AgentOS"** — três causas comuns (resolva nesta ordem):
  1. **Bloqueio de "loopback / Local Network Access" do Chrome (o mais provável).** No Console do navegador (F12) aparece: *"blocked by CORS policy: Permission was denied for this request to access the `loopback` address space."* É uma trava de segurança do Chrome que impede um site público (`os.agno.com`) de acessar o `localhost`. **Solução:** clique no ícone de rede bloqueada na barra de endereço e **permita** o acesso à rede local para o site; OU abra `chrome://flags`, busque por `network`, e desative **"Local Network Access Checks"** / **"Block insecure private network requests"**, depois clique em **Relaunch**.
  2. **IPv6 x IPv4 (Windows):** o navegador resolve `localhost` como `::1` (IPv6) mas o servidor escuta em `127.0.0.1` (IPv4). **Solução:** na URL do Studio use **`http://127.0.0.1:8000`** em vez de `localhost`. Sintoma: `curl http://127.0.0.1:8000/health` responde 200, mas `curl http://[::1]:8000/health` falha.
  3. **Private Network Access (preflight):** o `agente.py` já inclui um middleware que envia `Access-Control-Allow-Private-Network: true`. Depois de ajustar o navegador e a URL, clique em **REFRESH/UPDATE** no Studio.
- **`UnicodeEncodeError: 'charmap' ... \U0001f680` ao rodar `fastapi dev`** — o console do Windows (cp1252) não consegue imprimir o emoji do FastAPI. Rode `$env:PYTHONIOENCODING='utf-8'` antes de `fastapi dev agente.py` (ou use o Windows Terminal, que já usa UTF-8).
- **Memória não persiste** — confirme que `triagem_emails.db` foi criado na pasta e que `update_memory_on_run=True` está no `Agent`.
