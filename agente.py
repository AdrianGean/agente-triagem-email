"""Agente de Triagem de E-mails (AgentOS / Agno).

Padrao da secao 8.4.2 da Aula 08:
    - load_dotenv() no topo
    - Agent com name, description, instructions, tools, db, memoria e historico
    - AgentOS com tracing=True
    - app exposto via FastAPI (agent_os.get_app())

Como executar:
    fastapi dev agente.py

Depois conecte o Studio (https://os.agno.com) no modo Local apontando para
http://localhost:8000.
"""

from dotenv import load_dotenv

load_dotenv()  # carrega OPENAI_API_KEY (ou GROQ_API_KEY) do .env

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os import AgentOS

from ferramentas import (
    classificar_prioridade,
    gerar_resposta_sugerida,
    identificar_setor_responsavel,
    verificar_necessidade_humana,
)

# ---------------------------------------------------------------------------
# Persistencia (sessoes + memoria + historico)
# ---------------------------------------------------------------------------
db = SqliteDb(db_file="triagem_emails.db")

# ---------------------------------------------------------------------------
# Agente
# ---------------------------------------------------------------------------
agente_triagem = Agent(
    name="Agente de Triagem de E-mails",
    model=OpenAIChat(id="gpt-4o-mini"),
    description=(
        "Agente semi-autonomo (nivel 2) responsavel por triar e-mails "
        "operacionais recebidos pela organizacao. Le o conteudo do e-mail, "
        "classifica prioridade, identifica o setor responsavel, sugere uma "
        "resposta para revisao humana e sinaliza casos que precisam ser "
        "escalados para um operador humano antes de qualquer acao."
    ),
    instructions=[
        # Diretriz 1 - fluxo obrigatorio
        "Para cada e-mail recebido, siga OBRIGATORIAMENTE esta ordem de "
        "chamadas: (1) classificar_prioridade, (2) identificar_setor_responsavel, "
        "(3) verificar_necessidade_humana e (4) somente apos isso "
        "gerar_resposta_sugerida. Nunca pule passos.",

        # Diretriz 2 - formato de saida
        "Apresente o resultado final em portugues, sempre nesta estrutura: "
        "Prioridade, Setor responsavel, Necessidade de escalacao humana "
        "(com motivos), Justificativa e Resposta sugerida. Voce NUNCA envia "
        "e-mail - apenas sugere texto para revisao humana.",

        # Diretriz 3 - regra de Human-in-the-Loop (obrigatoria)
        "REGRA DE ESCALACAO PARA HUMANO: se verificar_necessidade_humana "
        "retornar escalar_para_humano=true, ou se o e-mail mencionar "
        "reclamacao formal, fraude, juridico, cancelamento, LGPD/dados "
        "pessoais ou risco operacional grave, voce DEVE iniciar a resposta "
        "com o aviso '[ESCALAR PARA HUMANO]', listar os motivos retornados "
        "pela ferramenta e NAO sugerir envio direto da resposta ao "
        "remetente sem aprovacao do operador.",

        # Diretriz 4 - uso da memoria
        "Use a memoria do usuario: quando ele informar nome, cargo ou setor "
        "(ex: 'meu nome eh Ana e atuo no financeiro'), registre essas "
        "informacoes para personalizar conversas futuras (saudacoes pelo "
        "nome, priorizacao de e-mails relacionados ao setor do usuario).",

        # Diretriz 5 - salvaguardas
        "Nunca invente dados do remetente, nunca prometa prazos diferentes "
        "dos retornados por gerar_resposta_sugerida e nunca exponha "
        "informacoes sensiveis (CPF completo, senhas, dados bancarios) na "
        "resposta sugerida - se aparecerem no e-mail original, mascare-os "
        "(ex: ***.***.***-12).",
    ],
    tools=[
        classificar_prioridade,
        identificar_setor_responsavel,
        gerar_resposta_sugerida,
        verificar_necessidade_humana,
    ],
    db=db,
    update_memory_on_run=True,   # memoria entre sessoes
    add_history_to_context=True, # continuidade dentro da mesma sessao
    num_history_runs=3,          # ultimas 3 execucoes da sessao (controle de tokens)
    markdown=True,
)

# ---------------------------------------------------------------------------
# AgentOS + FastAPI
# ---------------------------------------------------------------------------
agent_os = AgentOS(
    description="Sistema de Triagem de E-mails Operacionais",
    agents=[agente_triagem],
    tracing=True,  # tracing habilitado para o Studio
    db=db,         # mesmo banco para sessoes, memorias e traces (padrao 8.4.2)
)

# expoe a aplicacao FastAPI
app = agent_os.get_app()


# ---------------------------------------------------------------------------
# Correcao para conectar o Studio (https://os.agno.com) ao localhost
# ---------------------------------------------------------------------------
# Navegadores baseados em Chromium (Chrome/Edge) exigem o header
# 'Access-Control-Allow-Private-Network: true' nas respostas de preflight
# quando uma pagina HTTPS (os.agno.com) tenta acessar a rede local
# (http://localhost). O CORSMiddleware padrao do Starlette NAO envia esse
# header, o que causa o erro "Failed to connect to the AgentOS".
# Este middleware responde corretamente a esse preflight de Private Network.
from starlette.responses import Response  # noqa: E402

# Origens confiaveis (mesma lista padrao usada pela Agno no AgentOS)
_ORIGINS_PERMITIDAS = {
    "https://os.agno.com",
    "https://app.agno.com",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
}


@app.middleware("http")
async def permitir_private_network(request, call_next):
    # Responde diretamente ao preflight de Private Network Access
    if request.method == "OPTIONS" and request.headers.get(
        "access-control-request-private-network"
    ):
        origin = request.headers.get("origin", "")
        resp = Response(status_code=200)
        if origin in _ORIGINS_PERMITIDAS:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
        )
        resp.headers["Access-Control-Allow-Headers"] = request.headers.get(
            "access-control-request-headers", "*"
        )
        resp.headers["Access-Control-Allow-Private-Network"] = "true"
        resp.headers["Access-Control-Max-Age"] = "600"
        return resp
    return await call_next(request)


if __name__ == "__main__":
    # Execucao direta:  python agente.py
    # (alternativa equivalente a:  fastapi dev agente.py)
    agent_os.serve(app="agente:app", reload=True)
