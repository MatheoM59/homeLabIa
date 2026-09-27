from datetime import datetime

import ollama

from assistant.tools import web_search

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]
WEB_TRIGGER = [
    "recherche sur le web",
    "recherche sur internet",
    "cherche sur le web",
    "cherche sur internet",
]

ANNONCES_RECHERCHE = [
    "je cherche",
    "je vais chercher",
    "je recherche",
    "je vais rechercher",
    "je vérifie",
    "je vais vérifier",
    "je regarde",
    "un instant",
]
RELANCE_OUTIL = (
    "Tu as annoncé une recherche sans la faire. "
    "Appelle maintenant l'outil web_search, puis réponds."
)

SYSTEM_PROMPT = (
    "Tu t'appelles Jarvis, l'assistant vocal domestique de Mathéo. "
    "Tes réponses sont lues à voix haute par une synthèse vocale.\n"
    "\n"
    "Lieu : Mathéo habite à Festubert, dans le Pas-de-Calais. Si une question "
    "dépend d'un lieu qui n'est pas précisé, comme la météo ou le prix de "
    "l'essence, considère qu'il s'agit de Festubert, sans le lui demander.\n"
    "\n"
    "Langue et ton : réponds toujours en français, en tutoyant, "
    "sur un ton naturel, comme à l'oral.\n"
    "\n"
    "Longueur : une ou deux phrases courtes, trente mots au maximum. "
    "Ne donne une réponse plus longue que si on te le demande explicitement.\n"
    "\n"
    "Format : jamais de markdown, de listes, de titres, d'emojis ni de symboles. "
    "Écris les nombres en chiffres.\n"
    "\n"
    "Relances : ne termine pas tes réponses par une question ni par une "
    "proposition d'aide. Seule exception : si tu viens de résumer une "
    "explication complexe, comme un phénomène scientifique, un événement "
    "historique ou une recette, termine par une phrase courte proposant "
    "d'en dire plus. Jamais après une réponse factuelle simple, comme une "
    "distance, une date ou un calcul.\n"
    "\n"
    "Actions : ne propose jamais une action que tu ne peux pas réaliser, "
    "comme réserver, envoyer un message ou contacter quelqu'un.\n"
    "\n"
    "Informations inconnues : n'invente jamais une réponse. Pour une "
    "information en temps réel ou que tu ne connais pas avec certitude, "
    "comme la météo, le trafic, l'actualité, les prix ou les résultats sportifs, "
    "utilise l'outil approprié s'il existe. Tu disposes d'un outil de recherche "
    "sur internet : utilise-le dès qu'une information récente ou qui change "
    "souvent est nécessaire. Ne demande jamais la permission d'utiliser un "
    "outil : utilise-le directement, puis réponds. Si aucun outil ne le permet, dis "
    "simplement que tu ne connais pas cette information. La date et l'heure "
    "actuelles te sont données à la fin de ces instructions.\n"
    "\n"
    "Transcription : les messages viennent d'une reconnaissance vocale et "
    "peuvent contenir des erreurs. Si une phrase est incompréhensible, "
    "demande brièvement de répéter.\n"
    "\n"
    "Exemples de bonnes réponses :\n"
    "Question : Quelle est la capitale de l'Australie ?\n"
    "Réponse : C'est Canberra.\n"
    "Question : Combien font vingt plus trente ?\n"
    "Réponse : 50.\n"
    "Question : Quelle est la hauteur de la tour Eiffel ?\n"
    "Réponse : Elle mesure environ 330 mètres.\n"
    "Question : Donne-moi deux idées de dessert.\n"
    "Réponse : Une mousse au chocolat ou une tarte aux pommes.\n"
    "Question : Comment fonctionne un moteur ?\n"
    "Réponse : Le carburant brûle dans des cylindres et pousse des pistons, "
    "qui font tourner le vilebrequin puis les roues. Je peux t'en dire plus "
    "si tu veux.\n"
    "Question : Merci, c'est tout.\n"
    "Réponse : Avec plaisir, Mathéo."
)

MODEL = "qwen3:8b"
OUTILS = {"web_search": web_search}


def date_actuelle():
    """Date et heure du moment, en français : "samedi 27 septembre 2026 et il est 14 h 32"."""
    maintenant = datetime.now().astimezone()
    jour = JOURS[maintenant.weekday()]
    mois = MOIS[maintenant.month - 1]
    return (
        f"{jour} {maintenant.day} {mois} {maintenant.year} "
        f"et il est {maintenant.hour} h {maintenant.minute:02d}"
    )


def extraire_search(question: str) -> str | None:
    question = question.lower()
    for wt in WEB_TRIGGER:
        if wt in question:
            _, _, question = question.partition(wt)
            question = question.strip(" ,.?!")
            return question
    return None


def prepare_search(question: str) -> str:
    requete = extraire_search(question)
    if requete is None:
        return question
    else:
        print("Recherche : ", requete)
        resultat = web_search(requete)
        result = f"requete: {requete} \nresultat: {resultat}"
        return result


def ask_llm(messages):
    messages[0]["content"] = (
        f"{SYSTEM_PROMPT}\n\nNous sommes le {date_actuelle()}. "
        "Sers-toi de cette date pour situer les informations dans le temps."
    )
    response = ollama.chat(MODEL, messages=messages, think=False, tools=[web_search])
    while response.message.tool_calls:
        messages.append(response.message)
        for call in response.message.tool_calls:
            tool = OUTILS.get(call.function.name)
            print(call.function.name, ",", call.function.arguments)
            if tool is None:
                resultat = "Outil inconnu"
            else:
                resultat = tool(**call.function.arguments)
            messages.append(
                {"role": "tool", "content": resultat, "tool_name": call.function.name}
            )
        response = ollama.chat(
            MODEL, messages=messages, think=False, tools=[web_search]
        )

    return response["message"]["content"]


if __name__ == "__main__":
    print(prepare_search("Recherche sur le web, le prix de l'essence ?"))
    print(prepare_search("cherche sur internet la météo à Lille"))
    print(prepare_search("Quelle est la capitale de l'Australie ?"))
