"""Ferramentas customizadas do Agente de Triagem de E-mails.

Cada funcao deste modulo eh exposta ao agente como uma tool e implementa
um pedaco do processo descrito na Aula 08:

    1. classificar_prioridade           -> baixa / media / alta
    2. identificar_setor_responsavel    -> financeiro / rh / suporte / comercial / administrativo
    3. gerar_resposta_sugerida          -> texto para revisao humana (NUNCA enviado direto)
    4. verificar_necessidade_humana     -> regra de Human-in-the-Loop (escalacao)
"""

from typing import Dict, List


# ---------------------------------------------------------------------------
# Tool 1 - Prioridade
# ---------------------------------------------------------------------------
def classificar_prioridade(conteudo_email: str) -> Dict[str, str]:
    """Classifica a prioridade de um e-mail como baixa, media ou alta.

    Use sempre esta ferramenta como PRIMEIRO passo da triagem.

    Args:
        conteudo_email: Texto completo do e-mail recebido.

    Returns:
        Dicionario com as chaves 'prioridade' e 'justificativa'.
    """
    texto = (conteudo_email or "").lower()

    palavras_alta: List[str] = [
        "urgente", "imediato", "agora", "asap", "critico", "parado",
        "fraude", "reclamacao", "reclamação", "processo", "juridico", "jurídico",
        "prejuizo", "prejuízo", "cancelar", "cancelamento", "fora do ar",
        "down", "vazamento", "invasao", "invasão", "lgpd", "procon",
    ]
    palavras_media: List[str] = [
        "prazo", "atraso", "duvida", "dúvida", "pendente", "aguardando",
        "amanha", "amanhã", "hoje", "esta semana", "retorno",
    ]

    encontradas_alta = [p for p in palavras_alta if p in texto]
    encontradas_media = [p for p in palavras_media if p in texto]

    if encontradas_alta:
        return {
            "prioridade": "alta",
            "justificativa": (
                "Termos criticos detectados: " + ", ".join(encontradas_alta)
            ),
        }
    if encontradas_media:
        return {
            "prioridade": "media",
            "justificativa": (
                "Termos relacionados a prazo/pendencia detectados: "
                + ", ".join(encontradas_media)
            ),
        }
    return {
        "prioridade": "baixa",
        "justificativa": "Nenhum sinal de urgencia ou criticidade encontrado no texto.",
    }


# ---------------------------------------------------------------------------
# Tool 2 - Setor responsavel
# ---------------------------------------------------------------------------
def identificar_setor_responsavel(conteudo_email: str) -> Dict[str, str]:
    """Identifica o setor responsavel por tratar o e-mail.

    Args:
        conteudo_email: Texto completo do e-mail recebido.

    Returns:
        Dicionario com 'setor' (financeiro, rh, suporte, comercial ou
        administrativo) e 'palavras_chave_detectadas'.
    """
    texto = (conteudo_email or "").lower()

    setores: Dict[str, List[str]] = {
        "financeiro": [
            "pagamento", "boleto", "nota fiscal", "fatura", "cobranca", "cobrança",
            "reembolso", "deposito", "depósito", "transferencia", "transferência",
            "nf-e", "cnpj", "imposto", "tributo",
        ],
        "rh": [
            "ferias", "férias", "folha de pagamento", "contratacao", "contratação",
            "demissao", "demissão", "atestado", "beneficio", "benefício", "vale",
            "salario", "salário", "rescisao", "rescisão", "admissao", "admissão",
            "recursos humanos",
        ],
        "suporte": [
            "bug", "erro", "nao funciona", "não funciona", "sistema fora",
            "login", "senha", "acesso", "ticket", "chamado", "suporte tecnico",
            "suporte técnico", "indisponivel", "indisponível",
        ],
        "comercial": [
            "venda", "proposta", "orcamento", "orçamento", "contrato", "cliente",
            "lead", "negocio", "negócio", "produto", "preco", "preço", "desconto",
            "compra",
        ],
        "administrativo": [
            "documento", "certidao", "certidão", "protocolo", "agenda",
            "reuniao", "reunião", "ata", "comunicado", "expediente", "secretaria",
        ],
    }

    contagem: Dict[str, int] = {}
    palavras_detectadas: Dict[str, List[str]] = {}
    for setor, palavras in setores.items():
        encontradas = [p for p in palavras if p in texto]
        if encontradas:
            contagem[setor] = len(encontradas)
            palavras_detectadas[setor] = encontradas

    if not contagem:
        return {
            "setor": "administrativo",
            "palavras_chave_detectadas": (
                "nenhuma palavra-chave clara - encaminhado ao administrativo como padrao"
            ),
        }

    setor_escolhido = max(contagem, key=contagem.get)
    return {
        "setor": setor_escolhido,
        "palavras_chave_detectadas": ", ".join(palavras_detectadas[setor_escolhido]),
    }


# ---------------------------------------------------------------------------
# Tool 3 - Resposta sugerida
# ---------------------------------------------------------------------------
def gerar_resposta_sugerida(
    conteudo_email: str, setor: str, prioridade: str
) -> Dict[str, str]:
    """Gera uma resposta automatica SUGERIDA (para revisao humana).

    Esta ferramenta NUNCA envia e-mail. Apenas produz um rascunho que devera
    ser revisado por um operador humano antes de qualquer comunicacao externa.

    Args:
        conteudo_email: Texto do e-mail original.
        setor: Setor responsavel ja identificado.
        prioridade: Prioridade ja classificada (baixa, media ou alta).

    Returns:
        Dicionario com 'resposta_sugerida' e 'observacao'.
    """
    saudacoes = {
        "alta": "Recebemos sua mensagem e ja a classificamos como prioritaria.",
        "media": "Obrigado pelo seu contato.",
        "baixa": "Recebemos seu e-mail.",
    }
    encaminhamentos = {
        "financeiro": "Sua solicitacao foi encaminhada para o setor Financeiro.",
        "rh": "Sua solicitacao foi encaminhada para o setor de Recursos Humanos.",
        "suporte": "Sua solicitacao foi encaminhada para a equipe de Suporte Tecnico.",
        "comercial": "Sua solicitacao foi encaminhada para o setor Comercial.",
        "administrativo": "Sua solicitacao foi encaminhada para o setor Administrativo.",
    }
    prazos = {
        "alta": "Retornaremos em ate 2 horas uteis.",
        "media": "Retornaremos em ate 1 dia util.",
        "baixa": "Retornaremos em ate 3 dias uteis.",
    }

    prioridade = (prioridade or "baixa").lower()
    setor = (setor or "administrativo").lower()

    resposta = (
        "Prezado(a),\n\n"
        f"{saudacoes.get(prioridade, saudacoes['baixa'])} "
        f"{encaminhamentos.get(setor, encaminhamentos['administrativo'])} "
        f"{prazos.get(prioridade, prazos['baixa'])}\n\n"
        "Atenciosamente,\nEquipe de Atendimento."
    )

    return {
        "resposta_sugerida": resposta,
        "observacao": (
            "Este texto eh apenas uma SUGESTAO. Deve ser revisado por um "
            "humano antes do envio ao remetente."
        ),
    }


# ---------------------------------------------------------------------------
# Tool 4 - Human-in-the-Loop (escalacao)
# ---------------------------------------------------------------------------
def verificar_necessidade_humana(
    conteudo_email: str, prioridade: str
) -> Dict[str, object]:
    """Verifica se o caso exige escalacao para um operador humano.

    Esta ferramenta implementa a regra de Human-in-the-Loop do processo.
    O agente DEVE chama-la antes de finalizar a triagem.

    Args:
        conteudo_email: Texto do e-mail.
        prioridade: Prioridade ja classificada (baixa, media ou alta).

    Returns:
        Dicionario com 'escalar_para_humano' (bool), 'motivos' (lista) e
        'acao_recomendada' (str).
    """
    texto = (conteudo_email or "").lower()

    gatilhos: Dict[str, List[str]] = {
        "reclamacao formal": [
            "reclamacao", "reclamação", "reclamar", "insatisfacao", "insatisfação",
            "procon", "reclame aqui",
        ],
        "fraude/seguranca": [
            "fraude", "golpe", "invasao", "invasão", "vazamento", "phishing",
            "hacker", "roubo de dados",
        ],
        "juridico": [
            "juridico", "jurídico", "advogado", "processo", "judicial",
            "intimacao", "intimação", "notificacao extrajudicial",
            "notificação extrajudicial",
        ],
        "cancelamento": [
            "cancelar contrato", "rescisao", "rescisão", "encerrar conta",
            "cancelar plano", "distrato",
        ],
        "saude/seguranca": [
            "acidente", "ferido", "emergencia medica", "emergência médica",
        ],
        "dados pessoais (LGPD)": [
            "lgpd", "dados pessoais", "direito do titular", "anpd",
        ],
    }

    motivos: List[str] = []
    for nome_gatilho, palavras in gatilhos.items():
        if any(p in texto for p in palavras):
            motivos.append(nome_gatilho)

    if (prioridade or "").lower() == "alta" and not motivos:
        motivos.append("alta prioridade com possivel impacto operacional")

    deve_escalar = len(motivos) > 0

    return {
        "escalar_para_humano": deve_escalar,
        "motivos": motivos if motivos else ["nenhum gatilho critico detectado"],
        "acao_recomendada": (
            "PAUSAR resposta automatica. Encaminhar caso para revisao humana "
            "antes de qualquer comunicacao externa."
            if deve_escalar
            else "Pode prosseguir com a resposta sugerida apos revisao padrao."
        ),
    }
