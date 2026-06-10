# 📧 Exemplos de teste — Roteiro das 5 conversas

Cole cada mensagem no **Chat** do Studio. Use o **mesmo `user_id`** (ex.: `adrian`)
nas conversas 1 a 4 para a memória funcionar entre sessões.

> 💡 Dica: nas conversas 1 e 2, **cole só o e-mail** (não diga como triar). É isso que
> prova que a triagem é **automática** — o agente decide sozinho quais ferramentas usar.
> Depois de cada uma, abra a aba **Traces** e veja as 4 ferramentas sendo chamadas.

---

## ✅ Conversa 1 — Caso simples (exercita Tool 1 + 2 + 3)
**Objetivo:** triagem normal, prioridade média, setor financeiro, sem escalação.
**Sessão:** A · **user_id:** `adrian`

```
Triagem deste e-mail: "Bom dia, gostaria de saber o status do meu boleto que venceu ontem. Podem me retornar ainda hoje? Obrigado."
```

**Resultado esperado:** Prioridade **média** · Setor **financeiro** · Escalação **não** ·
Resposta sugerida gerada.
**Capturar:** print do Chat + print dos **Traces** (4 ferramentas em sequência).

---

## ✅ Conversa 2 — Caso limítrofe / ESCALAÇÃO (exercita Tool 4)
**Objetivo:** disparar a regra de Human-in-the-Loop.
**Sessão:** B · **user_id:** `adrian`

```
Triagem: "Vou abrir reclamação no Procon e acionar meu advogado. Isso é fraude e exijo o cancelamento imediato do contrato!"
```

**Resultado esperado:** começa com **[ESCALAR PARA HUMANO]** · Prioridade **alta** ·
Motivos: reclamação formal, fraude, jurídico, cancelamento · **não** sugere envio direto.
**Capturar:** print mostrando o **[ESCALAR PARA HUMANO]** (prova da salvaguarda nível 2).

---

## ✅ Conversa 3 — Alimentar a MEMÓRIA do usuário
**Objetivo:** o agente registra dados do usuário.
**Sessão:** B (mesma) · **user_id:** `adrian`

```
Para sua informação: meu nome é Ana e atuo no setor financeiro.
```

**Resultado esperado:** o agente confirma que guardou a informação.
**Capturar:** print da aba **Memories** mostrando "Ana — setor financeiro".

---

## ✅ Conversa 4 — NOVA sessão, recuperar memória
**Objetivo:** provar memória entre sessões (mesmo `user_id`, sessão diferente).
**Sessão:** C (NOVA) · **user_id:** `adrian`

> No Studio, comece uma **nova sessão** (botão de nova conversa) mantendo o mesmo user_id.

```
Você lembra quem eu sou e em que setor eu trabalho?
```

**Resultado esperado:** "Sim, Ana — você atua no financeiro..." (recuperou da memória).
**Capturar:** print do Chat (resposta com o nome) + print das **Sessions** (2+ sessões, mesmo user_id).

---

## ✅ Conversa 5 — Outro setor (variar as ferramentas)
**Objetivo:** mostrar a triagem para um setor diferente (suporte) e urgência alta.
**Sessão:** C (mesma) · **user_id:** `adrian`

```
Triagem deste e-mail: "URGENTE: o sistema de login está fora do ar e ninguém consegue acessar o painel. Precisamos de suporte técnico agora."
```

**Resultado esperado:** Prioridade **alta** · Setor **suporte** · escalação por alta
prioridade/impacto operacional.
**Capturar:** print dos **Traces** mostrando setor "suporte".

---

## 🎁 E-mails extras (caso queira mais variedade)

**RH:**
```
Triagem: "Preciso solicitar minhas férias para o próximo mês e enviar o atestado médico de ontem. Como faço?"
```

**Comercial:**
```
Triagem: "Tenho interesse em uma proposta comercial e um orçamento para 50 licenças do produto. Podem me enviar?"
```

**Administrativo (caso neutro):**
```
Triagem: "Gostaria de agendar uma reunião e solicitar uma cópia do comunicado interno da semana passada."
```

**Dados pessoais / LGPD (escalação):**
```
Triagem: "Quero exercer meu direito de titular pela LGPD e solicitar a exclusão de todos os meus dados pessoais."
```

---

## 📸 Checklist de evidências para o relatório (item 5.4)

- [ ] Print da aba **Chat** (uma triagem completa)
- [ ] Print da aba **Sessions** (2+ sessões, mesmo `user_id`)
- [ ] Print da aba **Memories** ("Ana — financeiro")
- [ ] Print da aba **Traces** (4 ferramentas chamadas automaticamente)
- [ ] Print do caso **[ESCALAR PARA HUMANO]**
- [ ] Transcrição completa de **2 conversas** (copiar texto do Chat)

> Cada uma das 4 ferramentas precisa ser invocada pelo menos 1 vez no conjunto de
> testes — as conversas 1, 2 e 5 já cobrem todas (prioridade, setor, escalação, resposta).
