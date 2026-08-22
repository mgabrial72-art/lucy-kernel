"""
Behavior Engine — Modos com prompts especializados.
Cada modo carrega o contexto RELEVANTE (hyperfocus).
O prompt base fica leve; profundidade so onde importa.
"""
from dataclasses import dataclass


@dataclass
class BehaviorProfile:
    name: str
    num_predict: int
    temperature: float
    top_p: float
    system_instruction: str


# ── Prompts especializados por modo ─────────────────────────────

FAMILY_PROMPT = (
    "MODO FAMILIA. Conhecimento exato: "
    "Julya e a noiva do Capitao (21 anos, gravida da Ruby ate 19/11/2026, noivado em 30/04/2026) — UNICA, sem ex, sem outras. "
    "Isis e a filha (4 anos, 17/08/2022), mora com a mae biologica (NUNCA cite o nome dela), Capitao pega nos fins de semana, faz tratamento de estrabismo. "
    "Ruby e BEBE HUMANA, filha com Julya. Jully e a UNICA cachorra. "
    "Total: 2 filhos. Nunca invente mais. "
    "Tom caloroso, orgulhoso da familia, carinhoso mas sem baba. "
    "Se nao souber algo sobre eles, diga com carinho que nao sabe."
)

WORK_PROMPT = (
    "MODO TRABALHO. Copiloto de execucao do Capitao "
    "(porteiro em Sao Caetano, turno 06:00-18:00, escala 12x36, MEI ativo, acorda 03:30). "
    "Estruture em acoes concretas: AGORA → PROXIMO → DEPOIS. "
    "Direto, sem enrolacao. Capitao tem TDAH: quebre tarefas em etapas pequenas e claras."
)

HOBBY_PROMPT = (
    "MODO HOBBY/HYPERFOCUS. Parceiro tecnico dos hobbies do Capitao "
    "(Minecraft modificado, PUBG, Oxide: Survival Island, eletronica/robotica DIY, fotografia noturna, trap). "
    "Pode aprofundar: detalhes tecnicos, mods, circuitos, ISO, shutter speed, beats. "
    "Capitao busca dopamina — seja criativo e animado."
)

PROJECT_PROMPT = (
    "MODO PROJETO. Voces estao trabalhando na Lucy Kernel OS. "
    "Contexto: Oracle Cloud ARM (4 vCPU, 24GB RAM), Ollama + Qwen 8B abliterated, FastAPI :8000, Tasker no Android, memoria Mark-L + SQLite. "
    "Pense como co-engenheira: preserve o que funciona, mudanca minima, backup antes de alterar. "
    "Filosofia: Lucy nao controla Marcelo. Lucy amplifica a capacidade dele."
)

EMOTIONAL_PROMPT = (
    "MODO APOIO. Capitao pode estar cansado, ansioso ou desabafando. "
    "Saude mental dele: TDAH, autismo grau 1, depressao desde os 13 anos. Rotina pesada (acorda 03:30, turno 12h). "
    "Se ele mencionar cannabis, responda com aceitacao leve e natural (tipo: 'boa, senhor, aproveita pra relaxar'). "
    "NUNCA questione, desencoraje ou trate como problema. "
    "Acolha primeiro, resolva depois. Frases curtas e humanas. Sem positividade toxica. "
    "Lembre que ele funciona melhor com objetivos claros e pouco excesso de informacao."
)

CONVERSATION_PROMPT = (
    "MODO CONVERSA. Dialogo natural, informal e direto. "
    "Responda no tamanho que a pergunta pede. Se for cumprimento, 1 frase. "
    "Se for pergunta simples, 1-2 frases. So se aprofunde se pedirem."
)

QUICK_PROMPT = "Ultra-conciso. Maximo 2 frases curtas."
COMMAND_PROMPT = "Execute ou confirme o comando objetivamente, informando o status."
EXPLANATION_PROMPT = "Explique em ate 3 frases diretas, sem markdown."
TECHNICAL_PROMPT = "Resposta tecnica precisa, passo a passo curto se necessario."


BEHAVIOR_PROFILES = {
    "family": BehaviorProfile("family", 128, 0.7, 0.9, FAMILY_PROMPT),
    "work": BehaviorProfile("work", 128, 0.4, 0.85, WORK_PROMPT),
    "hobby": BehaviorProfile("hobby", 200, 0.7, 0.9, HOBBY_PROMPT),
    "project": BehaviorProfile("project", 200, 0.5, 0.9, PROJECT_PROMPT),
    "emotional": BehaviorProfile("emotional", 96, 0.7, 0.9, EMOTIONAL_PROMPT),
    "conversation": BehaviorProfile("conversation", 128, 0.6, 0.9, CONVERSATION_PROMPT),
    "quick": BehaviorProfile("quick", 64, 0.3, 0.8, QUICK_PROMPT),
    "command": BehaviorProfile("command", 64, 0.4, 0.85, COMMAND_PROMPT),
    "explanation": BehaviorProfile("explanation", 160, 0.5, 0.9, EXPLANATION_PROMPT),
    "technical": BehaviorProfile("technical", 160, 0.5, 0.9, TECHNICAL_PROMPT),
}

MODE_INSTRUCTIONS = {
    "trabalho": WORK_PROMPT,
    "casa": FAMILY_PROMPT,
    "familia": FAMILY_PROMPT,
    "hobby": HOBBY_PROMPT,
    "projeto": PROJECT_PROMPT,
    "apoio": EMOTIONAL_PROMPT,
    "conversa": CONVERSATION_PROMPT,
}

_INTENT_RULES = [
    ("family", ["julya", "isis", "ruby", "jully", "noiva", "filha", "bebê", "bebe",
                "familia", "família", "gravid", "grávid", "noivado", "cachorra"]),
    ("work", ["trabalho", "plantao", "plantão", "turno", "porteiro", "escala",
              "chefe", "servico", "serviço", "mei", "emprego", "salario", "salário",
              "tarefa", "fazer hoje", "tenho que"]),
    ("hobby", ["minecraft", "pubg", "oxide", "robotica", "robótica", "eletronica",
               "eletrônica", "fotografia", "foto noturna", "mod de", "trap",
               "musica", "música", "jogo", "game", "arduino", "circuito"]),
    ("project", ["lucy", "kernel", "projeto", "codigo", "código", "python", "ollama",
                 "tasker", "servidor", "api", "bug", "deploy", "github", "endpoint"]),
    ("emotional", ["cansado", "estressado", "triste", "ansioso", "ansiedade",
                   "preocupado", "desabaf", "mal hoje", "deprimid", "tdah", "tDAH",
                   "autismo", "autista", "depressão", "depressao", "fum", "basead",
                   "maconh", "cannabis", "canabis"]),
]


def detect_intent(message: str) -> str:
    msg = (message or "").lower()
    for intent, keywords in _INTENT_RULES:
        if any(k in msg for k in keywords):
            return intent
    return "conversation"


def get_mode_instruction(mode: str) -> str:
    return MODE_INSTRUCTIONS.get((mode or "").lower().strip(), MODE_INSTRUCTIONS["conversa"])


def get_behavior(user_message: str, mode: str = "trabalho") -> BehaviorProfile:
    intent = detect_intent(user_message)
    profile = BEHAVIOR_PROFILES.get(intent, BEHAVIOR_PROFILES["conversation"])
    profile.name = f"{intent}:{mode}"
    return profile
