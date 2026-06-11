"""Interface web local do Agente de Triagem de E-mails.

Pagina unica servida pelo proprio FastAPI do AgentOS em /ui.
Cumpre o papel previsto no mapeamento da Aula 08 (interface para inserir e
visualizar o conteudo do e-mail), sem dependencias extras: o front-end chama
o endpoint REST /agents/agente-de-triagem-de-e-mails/runs do proprio AgentOS.
"""

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth import usuario_logado

AGENTE_SLUG = "agente-de-triagem-de-e-mails"

PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Triagem de E-mails — Interface Local</title>
<style>
  :root {
    --bg: #f4f6f9; --card: #ffffff; --borda: #dde3ea;
    --texto: #1f2937; --suave: #6b7280; --azul: #2563eb;
    --vermelho: #dc2626; --verde: #16a34a; --amarelo: #d97706;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Segoe UI", system-ui, sans-serif;
    background: var(--bg); color: var(--texto);
    min-height: 100vh; padding: 24px;
  }
  .container { max-width: 880px; margin: 0 auto; }
  header { margin-bottom: 20px; }
  header h1 { font-size: 1.5rem; }
  header p { color: var(--suave); font-size: .95rem; margin-top: 4px; }
  .card {
    background: var(--card); border: 1px solid var(--borda);
    border-radius: 12px; padding: 20px; margin-bottom: 16px;
  }
  label { font-size: .8rem; font-weight: 600; color: var(--suave);
          text-transform: uppercase; letter-spacing: .04em; }
  .linha { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
  .campo { flex: 1; min-width: 180px; }
  input, textarea {
    width: 100%; border: 1px solid var(--borda); border-radius: 8px;
    padding: 10px 12px; font-size: .95rem; font-family: inherit;
    margin-top: 4px; background: #fbfcfe;
  }
  textarea { min-height: 130px; resize: vertical; }
  input:focus, textarea:focus { outline: 2px solid var(--azul); border-color: transparent; }
  .acoes { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  button {
    border: 0; border-radius: 8px; padding: 11px 22px; font-size: .95rem;
    font-weight: 600; cursor: pointer; transition: opacity .15s;
  }
  button:hover { opacity: .88; }
  button:disabled { opacity: .5; cursor: wait; }
  .btn-principal { background: var(--azul); color: #fff; }
  .btn-secundario { background: #e5e9f0; color: var(--texto); }
  .status { font-size: .85rem; color: var(--suave); }
  .conversa { display: flex; flex-direction: column; gap: 14px; }
  .msg { border-radius: 12px; padding: 14px 16px; max-width: 92%;
         line-height: 1.55; font-size: .95rem; white-space: normal; }
  .msg.user { align-self: flex-end; background: var(--azul); color: #fff; }
  .msg.agente { align-self: flex-start; background: var(--card);
                border: 1px solid var(--borda); }
  .msg.agente.escalar { border: 2px solid var(--vermelho); }
  .selo {
    display: inline-block; font-size: .72rem; font-weight: 700;
    padding: 2px 10px; border-radius: 999px; margin-bottom: 8px;
    background: #fee2e2; color: var(--vermelho);
  }
  .msg h3, .msg h4 { margin: 10px 0 4px; }
  .msg ul { margin: 4px 0 4px 20px; }
  .msg b { font-weight: 700; }
  .rodape { text-align: center; color: var(--suave); font-size: .8rem; margin-top: 20px; }
  .hist-cabecalho { display: flex; justify-content: space-between; align-items: center; }
  .btn-mini { padding: 6px 12px; font-size: .8rem; }
  .hist-item { padding: 10px 12px; border: 1px solid var(--borda); border-radius: 8px;
    margin-top: 8px; cursor: pointer; font-size: .88rem; display: flex;
    justify-content: space-between; gap: 10px; background: #fbfcfe; }
  .hist-item:hover { border-color: var(--azul); background: #eef4ff; }
  .hist-titulo { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .hist-data { color: var(--suave); white-space: nowrap; font-size: .78rem; }
  .hist-vazio { color: var(--suave); font-size: .85rem; margin-top: 8px; }
  .btn-apagar { background: transparent; border: 0; cursor: pointer;
    font-size: .9rem; padding: 2px 6px; border-radius: 6px; line-height: 1; }
  .btn-apagar:hover { background: #fee2e2; }
  .carregando { display: inline-block; width: 16px; height: 16px;
    border: 3px solid var(--borda); border-top-color: var(--azul);
    border-radius: 50%; animation: girar .7s linear infinite; vertical-align: middle; }
  @keyframes girar { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="container">
  <header style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap;">
    <div>
      <h1>📧 Triagem de E-mails Operacionais</h1>
      <p>Agente semi-autônomo (nível 2) — classifica prioridade e setor, sugere resposta
         e sinaliza casos para revisão humana. <b>Nenhum e-mail é enviado automaticamente.</b></p>
    </div>
    <div style="text-align:right; font-size:.85rem; color:var(--suave);">
      👤 <b>__EMAIL__</b><br>
      <a href="/logout" style="color:var(--vermelho); font-weight:600; text-decoration:none;">Sair</a>
    </div>
  </header>

  <div class="card">
    <div class="linha">
      <div class="campo">
        <label>Usuário (user_id)</label>
        <input id="userId" value="__EMAIL__" readonly title="Definido pelo login — as memórias do agente ficam vinculadas a este usuário">
      </div>
      <div class="campo">
        <label>Sessão (session_id)</label>
        <input id="sessionId" readonly>
      </div>
    </div>
    <label>Conteúdo do e-mail recebido</label>
    <textarea id="email" placeholder="Cole aqui o texto do e-mail para triagem..."></textarea>
    <div class="acoes" style="margin-top:12px">
      <button class="btn-principal" id="btnTriar" onclick="triar()">Triar e-mail</button>
      <button class="btn-secundario" onclick="novaSessao()">Nova sessão</button>
      <span class="status" id="status"></span>
    </div>
  </div>

  <div class="card">
    <div class="hist-cabecalho">
      <label>📜 Histórico de triagens</label>
      <button class="btn-secundario btn-mini" onclick="carregarHistorico()">Atualizar</button>
    </div>
    <div id="historico"><p class="hist-vazio">Carregando...</p></div>
  </div>

  <div class="conversa" id="conversa"></div>

  <p class="rodape">Interface local — os dados ficam no SQLite da sua máquina ·
     API: <code>/agents/__SLUG__/runs</code></p>
</div>

<script>
const SLUG = "__SLUG__";

function novaSessao() {
  document.getElementById("sessionId").value =
    "web-" + new Date().toISOString().slice(0,19).replace(/[:T-]/g,"");
  document.getElementById("conversa").innerHTML = "";
}
novaSessao();

function escapaHtml(t) {
  return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// conversor markdown-lite: negrito, titulos e listas
function renderiza(t) {
  let h = escapaHtml(t);
  h = h.replace(/^### (.*)$/gm, "<h4>$1</h4>");
  h = h.replace(/^## (.*)$/gm, "<h3>$1</h3>");
  h = h.replace(/\\*\\*(.+?)\\*\\*/g, "<b>$1</b>");
  h = h.replace(/^- (.*)$/gm, "<li>$1</li>");
  h = h.replace(/(<li>.*<\\/li>)/gs, "<ul>$1</ul>");
  h = h.replace(/\\n/g, "<br>");
  return h;
}

function adiciona(texto, classe) {
  const div = document.createElement("div");
  div.className = "msg " + classe;
  if (classe === "agente" && texto.includes("ESCALAR PARA HUMANO")) {
    div.classList.add("escalar");
    div.innerHTML = '<span class="selo">⚠ REVISÃO HUMANA OBRIGATÓRIA</span><br>' + renderiza(texto);
  } else {
    div.innerHTML = renderiza(texto);
  }
  document.getElementById("conversa").appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
}

async function triar() {
  const email = document.getElementById("email").value.trim();
  if (!email) { alert("Cole o conteúdo do e-mail primeiro."); return; }

  const btn = document.getElementById("btnTriar");
  const status = document.getElementById("status");
  btn.disabled = true;
  status.innerHTML = '<span class="carregando"></span> Agente analisando (chama as 4 ferramentas)...';

  adiciona(email, "user");
  document.getElementById("email").value = "";

  const fd = new FormData();
  fd.append("message", email);
  fd.append("stream", "false");
  fd.append("user_id", document.getElementById("userId").value || "adrian");
  fd.append("session_id", document.getElementById("sessionId").value);

  try {
    const r = await fetch(`/agents/${SLUG}/runs`, { method: "POST", body: fd });
    const data = await r.json();
    if (!r.ok) throw new Error(JSON.stringify(data).slice(0, 300));
    adiciona(data.content || "(sem conteúdo na resposta)", "agente");
    status.textContent = "Triagem concluída ✓ (registrada em Sessions/Traces)";
    carregarHistorico();
  } catch (e) {
    adiciona("Erro ao executar a triagem: " + e.message, "agente");
    status.textContent = "Falha — verifique se a chave da API está válida.";
  } finally {
    btn.disabled = false;
  }
}

// ------------------- Historico de triagens -------------------
function textoDoInput(ri) {
  // run_input pode ser string simples ou objeto/JSON {input_content: ...}
  if (ri && typeof ri === "object") return ri.input_content || JSON.stringify(ri);
  if (typeof ri === "string" && ri.trim().startsWith("{")) {
    try { const o = JSON.parse(ri); return o.input_content || ri; } catch {}
  }
  return ri || "(mensagem nao registrada)";
}

async function carregarHistorico() {
  const uid = document.getElementById("userId").value;
  const alvo = document.getElementById("historico");
  try {
    const r = await fetch(`/sessions?type=agent&user_id=${encodeURIComponent(uid)}`);
    const d = await r.json();
    const sessoes = d.data || [];
    alvo.innerHTML = "";
    if (!sessoes.length) {
      alvo.innerHTML = '<p class="hist-vazio">Nenhuma triagem anterior para este usuário.</p>';
      return;
    }
    for (const s of sessoes) {
      const div = document.createElement("div");
      div.className = "hist-item";
      div.onclick = () => abrirSessao(s.session_id);
      const titulo = document.createElement("span");
      titulo.className = "hist-titulo";
      titulo.textContent = (s.session_name || s.session_id).slice(0, 90);
      const data = document.createElement("span");
      data.className = "hist-data";
      data.textContent = s.created_at
        ? new Date(s.created_at).toLocaleString("pt-BR") : "";
      const btnApagar = document.createElement("button");
      btnApagar.className = "btn-apagar";
      btnApagar.title = "Apagar esta triagem do histórico";
      btnApagar.textContent = "🗑️";
      btnApagar.onclick = (ev) => { ev.stopPropagation(); apagarSessao(s.session_id); };
      div.append(titulo, data, btnApagar);
      alvo.appendChild(div);
    }
  } catch (e) {
    alvo.innerHTML = '<p class="hist-vazio">Erro ao carregar histórico: ' + e.message + '</p>';
  }
}

async function abrirSessao(sessionId) {
  const status = document.getElementById("status");
  status.textContent = "Carregando sessão...";
  try {
    const r = await fetch(`/sessions/${encodeURIComponent(sessionId)}/runs?type=agent`);
    const d = await r.json();
    const runs = Array.isArray(d) ? d : (d.data || []);
    document.getElementById("conversa").innerHTML = "";
    for (const run of runs) {
      adiciona(textoDoInput(run.run_input), "user");
      adiciona(run.content || "(sem resposta)", "agente");
    }
    // retoma a sessao aberta: novas triagens continuam nela
    document.getElementById("sessionId").value = sessionId;
    status.textContent = `Sessão "${sessionId}" carregada (${runs.length} triagem(ns)) — novas mensagens continuam nela.`;
  } catch (e) {
    status.textContent = "Erro ao abrir sessão: " + e.message;
  }
}

async function apagarSessao(sessionId) {
  if (!confirm("Apagar esta triagem do histórico? Esta ação não pode ser desfeita.")) return;
  const status = document.getElementById("status");
  try {
    const r = await fetch(`/sessions/${encodeURIComponent(sessionId)}`, { method: "DELETE" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    // se a sessao apagada era a aberta, comeca uma nova e limpa a conversa
    if (document.getElementById("sessionId").value === sessionId) novaSessao();
    status.textContent = "Triagem apagada do histórico. 🗑️";
    carregarHistorico();
  } catch (e) {
    status.textContent = "Erro ao apagar: " + e.message;
  }
}

// Ctrl+Enter envia
document.getElementById("email").addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") triar();
});

carregarHistorico();
</script>
</body>
</html>"""


def registrar_interface(app):
    """Registra a rota GET /ui no app FastAPI do AgentOS (exige login)."""

    @app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
    def interface_web(request: Request):
        email = usuario_logado(request)
        if not email:
            return RedirectResponse("/login", status_code=303)
        pagina = PAGINA.replace("__SLUG__", AGENTE_SLUG).replace("__EMAIL__", email)
        return pagina
