import time

# Le contexte de qwen3:8b est de 4096 tokens (~12 000 caractères en français) pour tout :
# prompt système (~3 000 caractères), historique, résultats de recherche et réponse.
# On réserve ~7 000 caractères à la conversation, prompt système non compris.
TAILLE_MAX_HISTORIQUE = 7000

# Au réveil, si personne n'a parlé depuis ce délai, on repart d'une conversation vierge.
INACTIVITE_MAX = 10 * 60  # secondes

RESULTATS_RETIRES = "[Résultats de recherche retirés de l'historique]"


def _contenu(message) -> str:
    """Contenu d'un message (dictionnaire ou objet renvoyé par Ollama), "" s'il n'en a pas."""
    return (message["content"] if "content" in message else None) or ""


def _index_derniere_question(messages) -> int:
    """Position du dernier message de l'utilisateur."""
    for i in range(len(messages) - 1, 0, -1):
        if messages[i]["role"] == "user":
            return i
    return len(messages)


def compacter(messages) -> None:
    """Remplace les résultats de recherche des échanges précédents par un court rappel.

    Les résultats de l'échange en cours sont gardés (le modèle en a besoin, y compris pour
    « dis-m'en plus »). Pour les plus anciens, la réponse de Jarvis en a gardé l'essentiel :
    inutile de conserver des milliers de caractères de pages web.
    """
    for message in messages[1 : _index_derniere_question(messages)]:
        if message["role"] == "tool":
            message["content"] = RESULTATS_RETIRES
        elif message["role"] == "user" and _contenu(message).startswith("requete:"):
            # Recherche forcée (prepare_search) : on ne garde que la ligne de la requête.
            message["content"] = _contenu(message).splitlines()[0]


def limiter(messages) -> None:
    """Supprime les plus anciens échanges tant que l'historique dépasse TAILLE_MAX_HISTORIQUE.

    Le message système (position 0) et l'échange en cours ne sont jamais supprimés. On coupe
    toujours juste avant une question de l'utilisateur, pour ne jamais laisser une réponse
    ou un résultat d'outil séparé de la question qui l'a provoqué.
    """
    while sum(len(_contenu(m)) for m in messages[1:]) > TAILLE_MAX_HISTORIQUE:
        questions = [i for i in range(2, len(messages)) if messages[i]["role"] == "user"]
        if not questions:
            return  # il ne reste que l'échange en cours
        del messages[1 : questions[0]]


def preparer_historique(messages) -> None:
    """À appeler avant chaque appel au modèle : compacte puis limite l'historique."""
    compacter(messages)
    limiter(messages)


def reinitialiser_si_inactif(messages, derniere_activite: float) -> None:
    """Vide l'historique (sauf le message système) si la dernière activité est trop ancienne."""
    if time.monotonic() - derniere_activite > INACTIVITE_MAX:
        del messages[1:]
