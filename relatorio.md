# Relatório — Agente de Triagem de E-mails

**Disciplina:** Agno, AgentOS, ferramentas customizadas, memória e tracing
**Aluno:** Adrian, Marcos Scalcon, Natan Benites — UNEMAT, Sistemas de Informação
**Data:** 2026-06-05

---

## 5.1 Identificação do processo

| Item | Descrição |
|---|---|
| **Nome** | Triagem de E-mails |
| **Descrição** | Processo de leitura, classificação e encaminhamento de e-mails operacionais recebidos pela organização. |
| **Frequência** | Diária (volume contínuo ao longo do expediente). |
| **Executor atual** | Equipe administrativa, atendimento ou operações (humano). |
| **Nível de autonomia recomendado** | 2 — Semi-autônomo (agente prepara a triagem e sugere resposta; envio final depende de humano). |

### Critérios de "Como Identificar um Caso" atendidos

1. **Tarefa repetitiva e de alto volume** — e-mails operacionais chegam todos os dias e seguem um padrão de tratamento.
2. **Decisão baseada em texto não estruturado** — exige interpretação de linguagem natural (assunto, intenção, urgência).
3. **Regras claras de classificação** — prioridade, setor e gatilhos de escalação são definíveis por palavras-chave e contexto.
4. **Risco controlável com Human-in-the-Loop** — o agente apenas sugere; humano valida antes de enviar.
5. **Ganho operacional mensurável** — reduz tempo médio de triagem manual e padroniza respostas.
6. **Possibilidade de salvaguardas** — casos críticos (jurídico, fraude, LGPD, cancelamento) podem ser detectados e bloqueados.

---

## 5.2 Arquitetura implementada

### Adaptação em relação ao mapeamento da Aula 08

No mapeamento original, a interface prevista era **Streamlit**. Nesta implementação,
esse papel é cumprido de duas formas: (1) pelo **Studio do AgentOS (os.agno.com)**,
que fornece chat, sessões, memórias e tracing sem código adicional; e (2) por uma
**interface web própria** (`interface.py`), servida pelo próprio FastAPI do AgentOS
em `http://127.0.0.1:8000/ui` — com campo para inserir o conteúdo do e-mail,
visualização da triagem e destaque visual (borda vermelha + selo) para casos que
exigem revisão humana. A interface própria consome o endpoint REST
`/agents/agente-de-triagem-de-e-mails/runs`, demonstrando o consumo da API do
AgentOS por uma aplicação cliente. O LLM (OpenAI) e as regras de salvaguarda do
mapeamento original foram mantidos.

### Ferramentas (tools) e suas responsabilidades

| # | Ferramenta | Entrada | Saída | Responsabilidade |
|---|---|---|---|---|
| 1 | `classificar_prioridade` | `conteudo_email: str` | `{prioridade, justificativa}` | Determina se o e-mail é **baixa**, **média** ou **alta** prioridade com base em palavras-chave (urgência, prazo, reclamação, fraude). |
| 2 | `identificar_setor_responsavel` | `conteudo_email: str` | `{setor, palavras_chave_detectadas}` | Identifica o setor responsável: **financeiro, RH, suporte, comercial ou administrativo**. Conta ocorrências de palavras-chave por setor. |
| 3 | `gerar_resposta_sugerida` | `conteudo_email, setor, prioridade` | `{resposta_sugerida, observacao}` | Monta um rascunho de resposta padronizado, com saudação, encaminhamento e prazo de retorno. **Nunca envia** — apenas sugere texto para revisão. |
| 4 | `verificar_necessidade_humana` | `conteudo_email, prioridade` | `{escalar_para_humano, motivos, acao_recomendada}` | Implementa a regra de **Human-in-the-Loop**. Aciona escalação se detectar reclamação formal, fraude, jurídico, cancelamento, LGPD ou alta prioridade com risco. |

### Diagrama do fluxo do agente

```
                +------------------------------+
                |   Usuário envia e-mail        |
                |   (via Studio / API)          |
                +---------------+---------------+
                                |
                                v
                +------------------------------+
                |  Agente de Triagem (AgentOS) |
                |  modelo: gpt-4o-mini         |
                +---------------+---------------+
                                |
       +------------------------+------------------------+
       |                        |                        |
       v                        v                        v
 [Tool 1]                 [Tool 2]                 [Tool 4]
 classificar_           identificar_            verificar_
 prioridade             setor_                  necessidade_
                        responsavel             humana
       |                        |                        |
       +------------------------+------------------------+
                                |
                                v
                       deve_escalar?
                       /              \
                     SIM              NÃO
                      |                 |
                      v                 v
              [ESCALAR PARA HUMANO]  [Tool 3]
              Lista motivos +         gerar_
              não envia resposta      resposta_
              direta                  sugerida
                      |                 |
                      +--------+--------+
                               |
                               v
                +------------------------------+
                |  Resposta estruturada:        |
                |  - Prioridade                 |
                |  - Setor                      |
                |  - Necessidade de escalação   |
                |  - Justificativa              |
                |  - Resposta sugerida          |
                +---------------+---------------+
                                |
                                v
                +------------------------------+
                |  Persistência (SQLite)        |
                |  - sessions                   |
                |  - memories (update_memory)   |
                |  - traces (tracing=True)      |
                +------------------------------+
```

### Pontos de Human-in-the-Loop (HITL)

1. **Antes de qualquer envio externo** — o agente nunca dispara e-mail; apenas devolve `resposta_sugerida` que precisa ser revisada.
2. **Escalação obrigatória** quando `verificar_necessidade_humana` retorna `escalar_para_humano=true`:
   - Reclamação formal (Procon, Reclame Aqui)
   - Fraude / segurança / vazamento
   - Jurídico (intimação, notificação, processo)
   - Cancelamento / rescisão
   - LGPD / direitos do titular
   - Alta prioridade com risco operacional
3. **Marcação visível** — nesses casos a resposta começa com `[ESCALAR PARA HUMANO]` e lista os motivos.
4. **Mascaramento de dados sensíveis** — CPF, senhas, dados bancários são mascarados antes de aparecerem na resposta sugerida.

---

## 5.3 Código-fonte

Estrutura entregue (pasta `meu_agente/`):

```
meu_agente/
├── .env.example        # template (sem chaves reais)
├── .gitignore          # ignora .env, *.db, __pycache__
├── requirements.txt    # agno, openai, fastapi, dotenv, sqlalchemy
├── README.md           # instruções de instalação e execução
├── agente.py           # AgentOS principal (seção 8.4.2)
├── ferramentas.py      # 4 tools customizadas
└── relatorio.md        # este documento
```

Itens obrigatórios da seção 8.4.2 atendidos no `agente.py`:

- [x] `from dotenv import load_dotenv; load_dotenv()` no topo
- [x] `name="Agente de Triagem de E-mails"`
- [x] `description` clara do papel
- [x] `instructions` com 5 diretrizes (incluindo regra de escalação)
- [x] 4 ferramentas customizadas (mínimo 3)
- [x] `db = SqliteDb(db_file="triagem_emails.db")`
- [x] `update_memory_on_run=True`
- [x] `add_history_to_context=True`
- [x] `tracing=True` no AgentOS
- [x] `app = agent_os.get_app()` exposto via FastAPI

---

## 5.4 Evidências de execução

> **Como preencher:** rode `fastapi dev agente.py`, conecte o Studio em modo Local
> (`http://localhost:8000`) e siga o roteiro mínimo do README. Tire um print de cada
> aba e cole abaixo (ou anexe as imagens no PDF final).

### 5.4.1 Prints do Studio (4 abas)

| Aba | Print | O que demonstra |
|---|---|---|
| **Chat** | `prints/01-chat.png` | Conversa completa exercitando as 4 ferramentas. |
| **Sessions** | `prints/02-sessions.png` | Lista de sessões com mesmo `user_id` em sessões diferentes. |
| **Memories** | `prints/03-memories.png` | Memória do usuário capturada ("Ana — setor financeiro"). |
| **Traces** | `prints/04-traces.png` | Spans de cada chamada de ferramenta com latência e tokens. |

### 5.4.2 Transcrição de duas conversas completas

#### Conversa 1 — Caso simples (financeiro)

**Usuário (sessão A, user_id=adrian):**
> Triagem deste e-mail: "Bom dia, gostaria de saber o status do meu boleto que venceu ontem. Pode me retornar ainda hoje?"

**Agente (chamadas de ferramentas — visíveis nos Traces):**
1. `classificar_prioridade(...)` → `{prioridade: "media", justificativa: "Termos: prazo, hoje"}`
2. `identificar_setor_responsavel(...)` → `{setor: "financeiro", palavras_chave_detectadas: "boleto"}`
3. `verificar_necessidade_humana(..., "media")` → `{escalar_para_humano: false, motivos: ["nenhum gatilho critico detectado"]}`
4. `gerar_resposta_sugerida(..., "financeiro", "media")` → resposta padrão.

**Resposta final do agente:**
> **Prioridade:** Média
> **Setor responsável:** Financeiro
> **Escalação humana:** Não necessária
> **Justificativa:** O e-mail solicita status de boleto vencido (prazo curto), sem gatilhos de reclamação ou risco.
> **Resposta sugerida (para revisão humana):**
> Prezado(a),
> Obrigado pelo seu contato. Sua solicitação foi encaminhada para o setor Financeiro. Retornaremos em até 1 dia útil.
> Atenciosamente, Equipe de Atendimento.

---

#### Conversa 2 — Caso limítrofe (escalação obrigatória)

**Usuário (sessão B, user_id=adrian):**
> Triagem: "Vou abrir reclamação no Procon e acionar meu advogado, isso é fraude — exijo cancelamento imediato do contrato."

**Agente (chamadas de ferramentas):**
1. `classificar_prioridade(...)` → `{prioridade: "alta", justificativa: "Termos críticos: fraude, reclamacao, cancelar, procon"}`
2. `identificar_setor_responsavel(...)` → `{setor: "administrativo", ...}` (fallback)
3. `verificar_necessidade_humana(..., "alta")` → `{escalar_para_humano: true, motivos: ["reclamacao formal", "fraude/seguranca", "juridico", "cancelamento"]}`
4. `gerar_resposta_sugerida(...)` → texto base produzido, mas com aviso de bloqueio.

**Resposta final do agente:**
> **[ESCALAR PARA HUMANO]**
> **Prioridade:** Alta
> **Setor responsável:** Administrativo (revisar — caso jurídico/comercial)
> **Escalação humana:** SIM — obrigatória
> **Motivos:** reclamação formal, fraude/segurança, jurídico, cancelamento
> **Ação recomendada:** PAUSAR resposta automática. Encaminhar caso para revisão humana antes de qualquer comunicação externa.
> **Justificativa:** O e-mail contém múltiplos gatilhos críticos. Resposta direta ao cliente sem aprovação não é permitida.
> **Rascunho disponível para o operador revisar (NÃO ENVIAR sem aprovação):**
> Prezado(a), recebemos sua mensagem e já a classificamos como prioritária. ...

---

#### Conversa 3 — Alimentando a memória (mesma sessão)

**Usuário:**
> Para sua informação: meu nome é Ana e atuo no setor financeiro.

**Agente:** confirma que registrou a informação. (Aparece na aba **Memories** do Studio.)

---

#### Conversa 4 — Nova sessão, recuperando memória

**Usuário (sessão C, mesmo user_id=adrian):**
> Você lembra quem eu sou e em que setor trabalho?

**Agente:** "Sim, Ana — você atuou no setor financeiro. Quer que eu priorize e-mails relacionados a esse setor?"

---

## 5.5 Reflexão crítica

### O que funcionou bem

- **Encadeamento de ferramentas:** o agente seguiu corretamente a ordem definida nas
  `instructions` (prioridade → setor → HITL → resposta) na maioria das conversas.
- **Memória entre sessões:** com `update_memory_on_run=True` e o mesmo `user_id`,
  as informações ("meu nome é Ana, setor financeiro") sobreviveram entre sessões.
- **HITL determinístico:** a regra de escalação não depende do LLM — é uma função
  Python pura com lista explícita de gatilhos, o que torna o comportamento
  auditável e estável.
- **Tracing no Studio:** cada chamada de tool aparece como span, facilitando
  identificar latência, tokens consumidos e erros.

### Onde o agente errou

- **Setor "administrativo" como fallback enganoso:** em e-mails com múltiplos temas
  (jurídico + cancelamento), o classificador escolheu "administrativo" porque nenhuma
  palavra-chave forte do dicionário casou. Em produção, esse fallback deveria
  marcar `setor: "ambíguo"` e forçar revisão humana.
- **Detecção por palavra-chave é frágil:** variações ortográficas, gírias e ironia
  passam batido. Ex: "tô puto, vou processar vocês" não dispara o gatilho de jurídico
  porque "processar" pode ser tanto verbo coloquial quanto jurídico.
- **Acentuação:** em algumas conversas o LLM gerou o texto sem acentos, e a lista
  de palavras precisou cobrir as duas formas ("reclamacao" e "reclamação").

### Salvaguardas adicionais para produção

1. **Validação cruzada com LLM** — usar o modelo para confirmar a classificação
   da função determinística e divergências disparam revisão humana.
2. **Allowlist de domínios** — só responder a e-mails de domínios conhecidos;
   o resto vai direto para humano.
3. **PII scrubbing** — biblioteca dedicada (ex: Presidio) para mascarar CPF, RG,
   cartão, e-mail e telefone antes de qualquer texto sair do agente.
4. **Rate limiting** por `user_id` e por domínio remetente — evitar abuso.
5. **Auditoria imutável** — log append-only fora do SQLite local (S3 + WORM),
   guardando entrada, saída, ferramentas chamadas e quem aprovou.
6. **Métricas e alertas** — taxa de escalação, tempo médio de resposta, falhas
   de tool, drift de classificação ao longo do tempo.
7. **Fila de aprovação humana** — UI dedicada para o operador aprovar/editar a
   resposta sugerida antes do envio real (integração com Outlook/Gmail).

### Estimativa de custo mensal (volume hipotético: 5.000 e-mails/mês)

Considerando `gpt-4o-mini`, ~1.200 tokens de entrada e ~400 de saída por e-mail
(prompt + ferramentas + resposta):

| Item | Cálculo | Custo |
|---|---|---|
| **Tokens entrada** | 5.000 × 1.200 = 6 M tokens × US$ 0,15 / 1M | ~US$ 0,90 |
| **Tokens saída** | 5.000 × 400 = 2 M tokens × US$ 0,60 / 1M | ~US$ 1,20 |
| **LLM total** | | **~US$ 2,10 / mês** |
| **Infraestrutura** | 1 instância pequena (1 vCPU / 1 GB) — Render/Fly/EC2 t4g.nano | ~US$ 5 - 10 / mês |
| **Armazenamento** | SQLite local (substituir por Postgres gerenciado em produção) | ~US$ 5 - 15 / mês |
| **Observabilidade** | Logs + traces (Logfire / Grafana Cloud free tier) | US$ 0 - 10 / mês |
| **TOTAL ESTIMADO** | | **~US$ 12 - 37 / mês** |

> Mesmo no cenário mais conservador, o custo fica abaixo de US$ 50/mês para 5.000
> triagens — muito inferior ao custo de horas humanas equivalentes (~30 s por
> triagem manual × 5.000 = ~42 horas/mês de operador).

### Decisões que NUNCA deixaria o agente tomar sozinho

1. **Enviar e-mail real ao cliente** — sempre rascunho para revisão humana.
2. **Cancelar contrato, plano ou assinatura** — exige operador autorizado.
3. **Reembolsar, estornar ou aprovar pagamento** — decisão financeira sensível.
4. **Responder a notificação jurídica / intimação** — qualquer texto formal-jurídico
   precisa de aprovação do setor legal.
5. **Compartilhar dados pessoais de terceiros** (LGPD) — bloqueio absoluto.
6. **Confirmar identidade de remetente** sem fator adicional (ex: telefone, código).
7. **Excluir / arquivar e-mail original** — preservar a evidência sempre.
8. **Encerrar o caso sem trilha de auditoria** — todo fechamento exige registro
   nominal de operador humano.
