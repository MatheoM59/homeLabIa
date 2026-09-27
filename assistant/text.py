import re
import unicodedata

from num2words import num2words

# Unités écrites après un nombre → forme prononcée par la synthèse vocale.
# Les plus longues d'abord, pour que "km" soit reconnu avant "m".
UNITES = {
    "°C": "degrés Celsius",
    "km/h": "kilomètres heure",
    "km": "kilomètres",
    "kg": "kilogrammes",
    "cm": "centimètres",
    "mm": "millimètres",
    "ml": "millilitres",
    "cl": "centilitres",
    "min": "minutes",
    "°": "degrés",
    "%": "pour cent",
    "€": "euros",
    "$": "dollars",
    "g": "grammes",
    "l": "litres",
    "m": "mètres",
    "h": "heures",
    "s": "secondes",
}

# Un nombre : "5600", "5 600" (espace ou espace insécable comme séparateur de milliers),
# avec éventuellement une partie décimale : "3,5" ou "3.5".
NOMBRE = r"\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?"

MOTIF_UNITE = re.compile(
    rf"({NOMBRE})\s*({'|'.join(re.escape(u) for u in UNITES)})(?![A-Za-zÀ-ÿ])"
)
MOTIF_HEURE = re.compile(r"\b(\d{1,2})\s*h\s*(\d{2})\b")
MOTIF_ORDINAL = re.compile(r"\b1(er|re)\b")
MOTIF_NOMBRE = re.compile(NOMBRE)

# num2words écrit "un" : on accorde au féminin devant ces noms ("une heure", "vingt et une minutes").
NOMS_FEMININS = [
    "heure", "minute", "seconde", "semaine", "journée", "fois", "personne",
    "cuillère", "pincée", "tasse", "tranche", "gousse", "tonne",
]
MOTIF_FEMININ = re.compile(rf"\bun ((?:{'|'.join(NOMS_FEMININS)})s?)\b")


def _nombre_en_lettres(texte):
    """Convertit un nombre écrit en chiffres ("5 600", "3,5") en toutes lettres."""
    brut = re.sub(r"[   ]", "", texte).replace(",", ".")
    valeur = float(brut) if "." in brut else int(brut)
    return num2words(valeur, lang="fr")


def _heure_en_lettres(match):
    """ "15h30" → "15 heures 30", "8h00" → "8 heures", "1h15" → "1 heure 15"."""
    heures, minutes = match.group(1), match.group(2)
    mot = "heure" if int(heures) <= 1 else "heures"
    return f"{int(heures)} {mot}" + ("" if minutes == "00" else f" {int(minutes)}")


def _unite_en_lettres(match):
    """Remplace l'abréviation d'unité, au singulier si le nombre vaut 1 ("1 l" → "1 litre")."""
    nombre, unite = match.group(1), UNITES[match.group(2)]
    if nombre == "1":
        premier_mot, _, reste = unite.partition(" ")
        if premier_mot.endswith("s"):
            unite = f"{premier_mot[:-1]} {reste}".strip()
    return f"{nombre} {unite}"


def _retirer_emojis(texte):
    """Retire les emojis et symboles décoratifs, que la synthèse vocale lirait mal."""
    return "".join(
        c
        for c in texte
        if unicodedata.category(c) != "So"
        and c not in "‍️"  # liaisons invisibles entre emojis
        and not "\U0001f3fb" <= c <= "\U0001f3ff"  # couleurs de peau (👍🏽)
    )


def clean_for_speech(texte):
    """Prépare une réponse du LLM pour la synthèse vocale.

    Garantit par le code les règles de forme qu'un petit modèle oublie :
    pas d'emojis ni de markdown, unités sans abréviation, nombres en lettres.
    """
    # Les unités passent avant les emojis : "°" est un symbole qui serait sinon retiré.
    texte = MOTIF_HEURE.sub(_heure_en_lettres, texte)
    texte = MOTIF_UNITE.sub(_unite_en_lettres, texte)
    texte = _retirer_emojis(texte)
    texte = texte.replace("*", "").replace("#", "")
    texte = MOTIF_ORDINAL.sub(lambda m: "premier" if m.group(1) == "er" else "première", texte)
    texte = MOTIF_NOMBRE.sub(lambda m: _nombre_en_lettres(m.group(0)), texte)
    texte = MOTIF_FEMININ.sub(r"une \1", texte)
    texte = re.sub(r"\s+", " ", texte).strip()
    # Un nombre converti en début de réponse perd sa majuscule ("4164." → "quatre mille…").
    return texte[:1].upper() + texte[1:]
