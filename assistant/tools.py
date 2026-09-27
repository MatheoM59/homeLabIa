from ddgs import DDGS
from ddgs.exceptions import DDGSException

LONGUEUR_MAX_PAGE = 2500
MOTS_MIN_PAR_LIGNE = 5


def _texte_utile(contenu: str) -> str:
    """Retire les lignes de menu d'une page, en gardant celles qui contiennent un chiffre (prix, scores…)."""
    lignes = []
    for ligne in contenu.splitlines():
        ligne = ligne.strip()
        if len(ligne.split()) >= MOTS_MIN_PAR_LIGNE or any(c.isdigit() for c in ligne):
            lignes.append(ligne)
    return "\n".join(lignes)


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
    try:
        results = DDGS().text(requete, region="fr-fr", max_results=3)
    except DDGSException:
        return "La recherche n'a donné aucun résultat."

    lignes = []
    for result in results:
        ligne = f"{result['title']} : {result['body']}"
        lignes.append(ligne)
    extraits = "\n".join(lignes)

    contenu_page = ""
    for result in results:
        try:
            page = DDGS().extract(result["href"], fmt="text_plain")
        except DDGSException:
            continue
        contenu_page = _texte_utile(str(page["content"]))[:LONGUEUR_MAX_PAGE]
        if contenu_page:
            break

    if not contenu_page:
        return extraits
    return (
        f"Extraits des résultats :\n{extraits}\n\n"
        f"Contenu de la page {result['href']} :\n{contenu_page}"
    )
