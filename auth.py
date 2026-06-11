"""Autenticacao simples (e-mail + senha) para a interface web local.

Implementacao didatica, sem dependencias externas:
    - Usuarios em SQLite (usuarios.db), senha com hash PBKDF2 + salt
      (nunca armazenada em texto puro)
    - Sessao via cookie HttpOnly com token aleatorio e expiracao de 8h
    - Rotas: /login, /registro, /logout

Protege a interface /ui. Os endpoints REST do AgentOS continuam abertos
localmente (necessario para o Studio); em producao, a protecao da API seria
feita com o JWT nativo do AgentOS.
"""

import hashlib
import secrets
import sqlite3
import time

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

DB_USUARIOS = "usuarios.db"
NOME_COOKIE = "sessao_triagem"
DURACAO_SESSAO_SEG = 8 * 60 * 60  # 8 horas


# ---------------------------------------------------------------------------
# Banco de usuarios e sessoes
# ---------------------------------------------------------------------------
def _conexao() -> sqlite3.Connection:
    con = sqlite3.connect(DB_USUARIOS)
    con.execute(
        "CREATE TABLE IF NOT EXISTS usuarios ("
        " email TEXT PRIMARY KEY,"
        " senha_hash TEXT NOT NULL,"
        " salt TEXT NOT NULL,"
        " criado_em REAL NOT NULL)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS sessoes ("
        " token TEXT PRIMARY KEY,"
        " email TEXT NOT NULL,"
        " expira_em REAL NOT NULL)"
    )
    return con


def _hash_senha(senha: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), 100_000
    ).hex()


def criar_usuario(email: str, senha: str) -> str | None:
    """Cria um usuario. Retorna mensagem de erro ou None se deu certo."""
    email = (email or "").strip().lower()
    if "@" not in email or "." not in email:
        return "Informe um e-mail valido."
    if len(senha or "") < 6:
        return "A senha precisa ter pelo menos 6 caracteres."
    con = _conexao()
    try:
        salt = secrets.token_hex(16)
        con.execute(
            "INSERT INTO usuarios (email, senha_hash, salt, criado_em) VALUES (?,?,?,?)",
            (email, _hash_senha(senha, salt), salt, time.time()),
        )
        con.commit()
        return None
    except sqlite3.IntegrityError:
        return "Este e-mail ja esta cadastrado."
    finally:
        con.close()


def verificar_credenciais(email: str, senha: str) -> bool:
    email = (email or "").strip().lower()
    con = _conexao()
    try:
        linha = con.execute(
            "SELECT senha_hash, salt FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
    finally:
        con.close()
    if not linha:
        return False
    senha_hash, salt = linha
    return secrets.compare_digest(senha_hash, _hash_senha(senha, salt))


def criar_sessao(email: str) -> str:
    token = secrets.token_urlsafe(32)
    con = _conexao()
    try:
        con.execute("DELETE FROM sessoes WHERE expira_em < ?", (time.time(),))
        con.execute(
            "INSERT INTO sessoes (token, email, expira_em) VALUES (?,?,?)",
            (token, email.strip().lower(), time.time() + DURACAO_SESSAO_SEG),
        )
        con.commit()
    finally:
        con.close()
    return token


def encerrar_sessao(token: str) -> None:
    con = _conexao()
    try:
        con.execute("DELETE FROM sessoes WHERE token = ?", (token,))
        con.commit()
    finally:
        con.close()


def usuario_logado(request: Request) -> str | None:
    """Retorna o e-mail do usuario logado, ou None se nao autenticado."""
    token = request.cookies.get(NOME_COOKIE)
    if not token:
        return None
    con = _conexao()
    try:
        linha = con.execute(
            "SELECT email, expira_em FROM sessoes WHERE token = ?", (token,)
        ).fetchone()
    finally:
        con.close()
    if not linha or linha[1] < time.time():
        return None
    return linha[0]


# ---------------------------------------------------------------------------
# Paginas (mesmo estilo visual da interface)
# ---------------------------------------------------------------------------
_ESTILO = """
  :root { --bg:#f4f6f9; --card:#fff; --borda:#dde3ea; --texto:#1f2937;
          --suave:#6b7280; --azul:#2563eb; --vermelho:#dc2626; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:"Segoe UI",system-ui,sans-serif; background:var(--bg);
         color:var(--texto); min-height:100vh; display:flex;
         align-items:center; justify-content:center; padding:24px; }
  .card { background:var(--card); border:1px solid var(--borda);
          border-radius:12px; padding:28px; width:100%; max-width:380px; }
  h1 { font-size:1.2rem; margin-bottom:4px; }
  p.sub { color:var(--suave); font-size:.85rem; margin-bottom:18px; }
  label { font-size:.75rem; font-weight:600; color:var(--suave);
          text-transform:uppercase; letter-spacing:.04em; }
  input { width:100%; border:1px solid var(--borda); border-radius:8px;
          padding:10px 12px; font-size:.95rem; margin:4px 0 14px;
          background:#fbfcfe; }
  input:focus { outline:2px solid var(--azul); border-color:transparent; }
  button { width:100%; border:0; border-radius:8px; padding:11px;
           font-size:.95rem; font-weight:600; cursor:pointer;
           background:var(--azul); color:#fff; }
  button:hover { opacity:.9; }
  .erro { background:#fee2e2; color:var(--vermelho); border-radius:8px;
          padding:10px 12px; font-size:.85rem; margin-bottom:14px; }
  .rodape { text-align:center; margin-top:16px; font-size:.85rem;
            color:var(--suave); }
  .rodape a { color:var(--azul); text-decoration:none; font-weight:600; }
"""

_PAGINA_LOGIN = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Entrar — Triagem de E-mails</title><style>__ESTILO__</style></head>
<body><div class="card">
  <h1>🔐 Triagem de E-mails</h1>
  <p class="sub">Entre para acessar a interface de triagem</p>
  __ERRO__
  <form method="post" action="/login">
    <label>E-mail</label>
    <input type="email" name="email" required autofocus>
    <label>Senha</label>
    <input type="password" name="senha" required>
    <button type="submit">Entrar</button>
  </form>
  <p class="rodape">Nao tem conta? <a href="/registro">Cadastre-se</a></p>
</div></body></html>"""

_PAGINA_REGISTRO = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cadastro — Triagem de E-mails</title><style>__ESTILO__</style></head>
<body><div class="card">
  <h1>📝 Criar conta</h1>
  <p class="sub">Cadastro para usar a interface de triagem</p>
  __ERRO__
  <form method="post" action="/registro">
    <label>E-mail</label>
    <input type="email" name="email" required autofocus>
    <label>Senha (minimo 6 caracteres)</label>
    <input type="password" name="senha" required minlength="6">
    <button type="submit">Cadastrar e entrar</button>
  </form>
  <p class="rodape">Ja tem conta? <a href="/login">Entrar</a></p>
</div></body></html>"""


def _render(template: str, erro: str = "") -> str:
    bloco_erro = f'<div class="erro">{erro}</div>' if erro else ""
    return template.replace("__ESTILO__", _ESTILO).replace("__ERRO__", bloco_erro)


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
def registrar_auth(app):
    """Registra as rotas /login, /registro e /logout no app FastAPI."""

    @app.get("/login", response_class=HTMLResponse, include_in_schema=False)
    def pagina_login(request: Request):
        if usuario_logado(request):
            return RedirectResponse("/ui", status_code=303)
        return _render(_PAGINA_LOGIN)

    @app.post("/login", include_in_schema=False)
    def fazer_login(email: str = Form(...), senha: str = Form(...)):
        if not verificar_credenciais(email, senha):
            return HTMLResponse(
                _render(_PAGINA_LOGIN, "E-mail ou senha incorretos."),
                status_code=401,
            )
        resposta = RedirectResponse("/ui", status_code=303)
        resposta.set_cookie(
            NOME_COOKIE,
            criar_sessao(email),
            max_age=DURACAO_SESSAO_SEG,
            httponly=True,
            samesite="lax",
        )
        return resposta

    @app.get("/registro", response_class=HTMLResponse, include_in_schema=False)
    def pagina_registro(request: Request):
        if usuario_logado(request):
            return RedirectResponse("/ui", status_code=303)
        return _render(_PAGINA_REGISTRO)

    @app.post("/registro", include_in_schema=False)
    def fazer_registro(email: str = Form(...), senha: str = Form(...)):
        erro = criar_usuario(email, senha)
        if erro:
            return HTMLResponse(_render(_PAGINA_REGISTRO, erro), status_code=400)
        resposta = RedirectResponse("/ui", status_code=303)
        resposta.set_cookie(
            NOME_COOKIE,
            criar_sessao(email),
            max_age=DURACAO_SESSAO_SEG,
            httponly=True,
            samesite="lax",
        )
        return resposta

    @app.get("/logout", include_in_schema=False)
    def fazer_logout(request: Request):
        token = request.cookies.get(NOME_COOKIE)
        if token:
            encerrar_sessao(token)
        resposta = RedirectResponse("/login", status_code=303)
        resposta.delete_cookie(NOME_COOKIE)
        return resposta
