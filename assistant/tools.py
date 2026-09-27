from ddgs import DDGS


def web_search(requete: str) -> str:
    """Recherche des informations récentes sur internet.

    Utilise cet outil pour l'actualité, les résultats sportifs, les prix,
    les événements récents, ou toute information que tu ne connais pas
    avec certitude.

    C'est un outil généraliste, à utiliser en dernier recours : ne l'utilise
    pas si un outil plus spécialisé existe pour la question, par exemple
    pour la météo.

    Args:
        requete: les mots-clés à rechercher, par exemple "dernier match PSG".
    """

    results = DDGS().text(requete, region="fr-fr", max_results=3)
    lignes = []
    for result in results:
        ligne = f"{result['title']} : {result['body']}"
        lignes.append(ligne)
    return "\n".join(lignes)
