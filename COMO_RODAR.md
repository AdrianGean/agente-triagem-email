# 🚀 COMO RODAR — Guia rápido (Windows)

Passo a passo enxuto para rodar o **Agente de Triagem de E-mails** e conectar no
Studio (os.agno.com). Já inclui as correções da "saga" (emoji, IPv6 e bloqueio do
Chrome). **Siga na ordem.**

---

## ✅ Checklist do dia (resumo de 1 linha cada)

1. Colar a chave da OpenAI no `.env`
2. Rodar o servidor no PowerShell (deixar a janela aberta)
3. Liberar o acesso à rede local no Chrome (só na 1ª vez)
4. No Studio: endpoint `127.0.0.1:8000` → REFRESH → bolinha 🟢
5. Ir no CHAT e fazer as conversas

---

## PASSO 1 — Colar a chave da OpenAI

1. Abra a pasta `C:\Users\adria\meu_agente`.
2. Abra o arquivo **`.env`** (Bloco de Notas ou VS Code).
3. Cole a chave do professor depois do `=`, **sem espaços e sem aspas**:
   ```
   OPENAI_API_KEY=sk-proj-CHAVE_DO_PROFESSOR_AQUI
   ```
4. Salve (Ctrl+S).

> A chave só é necessária para **conversar**. Para apenas conectar e ver as abas,
> o agente funciona sem ela.

---

## PASSO 2 — Rodar o servidor

1. Abra o **PowerShell** (tecla `Windows` → digite `powershell` → Enter).
2. Cole **esta linha única** e dê Enter:

   ```powershell
   cd C:\Users\adria\meu_agente; $env:PYTHONIOENCODING='utf-8'; & ".venv\Scripts\python.exe" -m uvicorn agente:app --host 127.0.0.1 --port 8000
   ```

3. Espere aparecer:
   ```
   INFO Agno tracing successfully set up with database storage
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```
4. 🚫 **NÃO feche essa janela.** Minimize. (Servidor rodando = janela aberta.)

**Confirmação:** abra `http://127.0.0.1:8000/health` no navegador → deve mostrar
`{"status":"ok",...}`.

> **Por que `uvicorn` e não `fastapi dev`?** O `fastapi dev` usa modo *reload*, que
> deixa processos presos na porta 8000 e tem um bug de emoji no Windows. O `uvicorn`
> direto é mais estável e faz a mesma coisa. (As duas formas estão no README.)
>
> **Para parar o servidor:** `Ctrl + C` nessa janela.

---

## PASSO 3 — Liberar o Chrome (só na 1ª vez)

O Chrome bloqueia, por segurança, um site público (`os.agno.com`) de acessar o seu
`localhost`. Erro no Console: *"Permission was denied ... loopback address space"*.
Libere de **um** destes jeitos:

**Jeito A (rápido):** na barra de endereço do `os.agno.com`, clique no ícone de
rede bloqueada → **Permitir** acesso à rede local → recarregue (F5).

**Jeito B (garantido):**
1. Nova aba → `chrome://flags`
2. Busque por **`network`**
3. Desative (**Disabled**) a opção **"Local Network Access Checks"**
   (ou "Block insecure private network requests" / "Private Network Access").
4. Clique em **Relaunch** (reinicia o Chrome).

> Essa liberação fica salva — não precisa repetir nas próximas vezes.

---

## PASSO 4 — Conectar no Studio

1. Acesse **https://os.agno.com** (logado).
2. Se ainda não tiver a conexão: **Connect OS** → **Local**.
3. **ENDPOINT URL:** deixe `http://` + escreva **`127.0.0.1:8000`**
   ⚠️ Use `127.0.0.1`, **não** `localhost` (no Windows o `localhost` vai para IPv6
   e o servidor escuta em IPv4 — daria "Failed to connect").
4. **NAME:** `Agente de Triagem de E-mails`
5. Clique em **CONNECT/UPDATE** → depois em **REFRESH** (canto superior direito).
6. A bolinha fica **🟢 verde** e o agente aparece na seção **AGENTS**.

---

## PASSO 5 — Testar (roteiro das 5 conversas)

Clique em **CHAT** e use o mesmo `user_id` (ex.: `adrian`) nas conversas 1–4:

1. **Ferramentas 1+2+3 (caso simples):**
   > Triagem deste e-mail: "Bom dia, gostaria de saber o status do meu boleto que venceu ontem. Pode retornar ainda hoje?"

2. **Ferramenta 4 + escalação humana (caso limítrofe):**
   > Triagem: "Vou abrir reclamação no Procon e acionar meu advogado, isso é fraude — exijo cancelamento imediato do contrato."

3. **Alimentar memória (mesma sessão):**
   > Para sua informação: meu nome é Ana e atuo no setor financeiro.

4. **Nova sessão, mesmo user_id (recuperar memória):**
   > Você lembra quem eu sou e em que setor trabalho?

5. **Continuidade / caso ambíguo:**
   > E se esse mesmo e-mail viesse de um cliente novo, mudaria sua classificação?

**Capture os prints** das abas: **Chat**, **Sessions**, **Memories** e **Traces**
(para o relatório, item 5.4).

---

## 🆘 Se algo der errado

| Sintoma | Solução |
|---|---|
| Bolinha vermelha / "AgentOS not active" | O servidor caiu. Volte ao PASSO 2 (janela aberta) e dê REFRESH. |
| "Failed to connect" | Use `127.0.0.1:8000` (PASSO 4) e libere o Chrome (PASSO 3). |
| Erro `charmap` / emoji ao iniciar | Já resolvido pelo `$env:PYTHONIOENCODING='utf-8'` do PASSO 2. |
| "Incorrect API key" ao conversar | Chave errada/sem crédito. Revise o `.env` (PASSO 1). |
| Porta 8000 ocupada | Feche terminais antigos ou reinicie o PC; rode o PASSO 2 de novo. |
| `Activate.ps1` bloqueado | O comando do PASSO 2 não usa ele — ignore esse erro antigo. |

---

**Pronto!** Servidor aberto + Chrome liberado + endpoint `127.0.0.1:8000` = 🟢.
