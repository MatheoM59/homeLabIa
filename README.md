# homeLabIa

Assistant vocal **100 % local** pour un homelab : on parle, une IA locale répond à voix haute. Aucun appel à un service cloud, tout tourne sur la machine.

> 🚧 Projet en cours — le pipeline est développé et testé sur Mac, puis sera migré sur un serveur Linux (Docker).

## Pipeline

```
Micro USB → Wake word → Speech-to-Text → LLM → Text-to-Speech → Enceinte
            openWakeWord  faster-whisper   Ollama     Piper
```

| Étape | Outil | Rôle |
|---|---|---|
| Wake word | [openWakeWord](https://github.com/dscripka/openWakeWord) | Détecte le mot d'activation et déclenche l'écoute |
| Speech-to-Text | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Transcrit la voix en texte (optimisé CPU) |
| LLM | [Ollama](https://ollama.com) + `qwen3:8b` | Génère la réponse, en local via `localhost:11434` |
| Text-to-Speech | [Piper](https://github.com/OHF-Voice/piper1-gpl) | Transforme la réponse en voix |
| Orchestration | Python 3.11 | Relie toutes les étapes |

## Prérequis

- **Python 3.11**
- **Ollama** installé, avec le modèle téléchargé :
  ```bash
  ollama pull qwen3:8b
  ```
- Un micro et une sortie audio

| | macOS | Debian / Ubuntu |
|---|---|---|
| Python 3.11 | `brew install python@3.11` | `sudo apt install python3.11 python3.11-venv` |
| PortAudio (capture micro) | inclus dans `sounddevice` | `sudo apt install libportaudio2` |
| ffmpeg | `brew install ffmpeg` | `sudo apt install ffmpeg` |

## Installation

```bash
git clone https://github.com/MatheoM59/homeLabIa.git
cd homeLabIa

python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Télécharger la voix de synthèse française (Piper, ~60 Mo, rangée dans `models/` qui est ignoré par git) :

```bash
python -m piper.download_voices fr_FR-siwis-medium --download_dir models
```

Télécharger le modèle du mot d'activation « Hey Jarvis » (openWakeWord, installé dans le dossier du paquet, à l'intérieur de `.venv`) :

```bash
python -c "from openwakeword.utils import download_models; download_models(['hey_jarvis'])"
```

`(.venv)` doit apparaître au début de la ligne du terminal. Il faut réactiver le venv (`source .venv/bin/activate`) à chaque nouveau terminal.

Après avoir ajouté une dépendance :

```bash
pip freeze > requirements.txt
```

## Lancement

Le serveur Ollama doit tourner (app Ollama, ou `ollama serve` dans un terminal séparé).

### Assistant

Depuis la racine du projet :

```bash
python -m assistant
```

L'assistant démarre **en veille** et attend le mot d'activation « **Hey Jarvis** » (prononcé à l'anglaise). Une fois réveillé : écoute jusqu'à la fin de la phrase (1,5 s de silence) → transcription → réponse de l'IA (avec mémoire de la conversation) → réponse lue à voix haute par Piper, et ainsi de suite. Si personne ne parle pendant 5 s, il retourne en veille. `Ctrl+C` pour l'arrêter.

Réglages dans `assistant/historique.py` : `TAILLE_MAX_HISTORIQUE` (taille maximale de la conversation gardée en mémoire, en caractères) et `INACTIVITE_MAX` (délai sans parler après lequel une nouvelle conversation commence).

Réglage dans `assistant/wakeword.py` : `DETECT_SEUIL` (score de 0 à 1 à partir duquel le mot est reconnu). Réglé à 0.2 : avec un accent français, les scores plafonnent autour de 0.4-0.5 (et moins quand on le dit sans y faire attention), alors que le bruit de fond reste sous 0.005. Si l'assistant se réveille tout seul, remonter le seuil ; si l'accent reste gênant, essayer le modèle `alexa` ou entraîner un mot personnalisé.

Réglages dans `assistant/audio.py` : `SEUIL_VOLUME` (volume RMS au-dessus duquel un bloc de 30 ms compte comme de la voix), `SILENCE_FIN`, `ATTENTE_MAX`, `DUREE_MAX`, `PAROLE_MIN` (durée de voix minimale pour qu'un enregistrement soit gardé : filtre les bruits brefs comme un clic ou un claquement).

### Scripts de test (une brique à la fois)

Test de la capture micro + transcription (enregistre 5 s puis affiche le texte) :

```bash
python scripts/test_micro.py
```

Au premier lancement, le modèle Whisper `small` (~500 Mo) est téléchargé : ça peut prendre une ou deux minutes sans rien afficher.

Discussion au clavier avec le LLM, avec mémoire de la conversation (`quit` pour sortir) :

```bash
python scripts/test_llm.py
```

## Pièges connus

- **`python3 --version` affiche 3.9 sur Mac** : c'est le Python d'Apple (`/usr/bin/python3`). Homebrew installe la 3.11 sous le nom `python3.11` → toujours créer le venv avec `python3.11 -m venv .venv`. Une fois le venv activé, `python` pointe bien sur la 3.11.
- **Autorisation micro sur macOS** : au premier enregistrement, macOS demande l'accès au micro pour le Terminal / VS Code. Si c'est refusé, l'enregistrement est silencieux et Whisper ne renvoie rien (à réactiver dans *Réglages Système → Confidentialité et sécurité → Micro*).
- **Format audio attendu par Whisper** : 16 000 Hz, mono, `float32`, tableau 1D (`sounddevice.rec()` renvoie un tableau `(N, 1)` → `.flatten()`).
- **Whisper invente du texte sur le silence** (« ... », « Merci d'avoir regardé »…) : il a appris sur des vidéos sous-titrées. `vad_filter=True` dans `transcribe()` coupe les passages sans voix → un silence renvoie une chaîne vide.
- **`python -m assistant`, pas `python assistant/__main__.py`** : le `-m` est nécessaire pour que les imports `from assistant.xxx import ...` fonctionnent.
- **`ConnectionError: Failed to connect to Ollama`** : le serveur Ollama ne tourne pas (terminal `ollama serve` fermé). Le relancer, ou utiliser l'app Ollama qui tourne en arrière-plan.
- **openWakeWord sur Mac** : `inference_framework="onnx"` obligatoire (le moteur par défaut, tflite, n'existe que sous Linux). L'audio doit être en `int16`, par blocs de 1280 échantillons (80 ms), et il faut appeler `reset()` après une détection, sinon le modèle se re-déclenche sur l'ancien audio gardé en mémoire.
- **Pylance souligne `predictions["hey_jarvis"]`** : `predict()` peut renvoyer un tuple si `timing=True`, Pylance ne peut pas savoir que ce n'est pas le cas → `# type: ignore` sur la ligne. Ce n'est pas une erreur d'exécution.
- **Voix Piper ralentie / trop grave** : les voix `medium` sont en 22 050 Hz, pas 16 000 → toujours jouer avec `chunk.sample_rate`.
- **Demander au LLM d'écrire les nombres en lettres le fait halluciner** (« soixante-cinq mille degrés » au lieu de 5 500 pour le Soleil). Il écrit en chiffres, et c'est `clean_for_speech()` qui convertit : ce qui peut être garanti par le code ne doit pas dépendre du modèle.
- **Les exemples du prompt sont imités à la lettre** : un exemple « Je ne connais pas la météo en temps réel » faisait refuser toute recherche (« Je ne connais pas le prix du Bitcoin »). Après l'ajout d'un outil, relire le prompt pour retirer les règles et exemples qui le contredisent. Qwen demandait aussi la permission avant de chercher → consigne « utilise-le directement ».
- **Fuseau horaire** : la date vient de l'horloge de la machine ; dans Docker, penser à `TZ=Europe/Paris`, sinon le conteneur est en UTC.
- **Portabilité** : pas de chemins en dur ni de libs spécifiques à macOS, le code doit tourner tel quel sur Linux.

## Roadmap

- [x] Ollama + `mistral-small3.2` fonctionnels en local
- [x] Environnement Python 3.11 (venv)
- [x] Installer faster-whisper + sounddevice
- [x] Script micro → transcription (`scripts/test_micro.py`)
- [x] Appel à Ollama avec consigne système + mémoire de conversation (`scripts/test_llm.py`)
- [x] Assembler le pipeline dans le package `assistant/` (micro → Whisper → Ollama)
- [x] Filtre VAD contre les hallucinations de Whisper sur le silence
- [x] Détection de fin de parole (seuil de volume RMS par blocs de 30 ms) au lieu d'un enregistrement de durée fixe
- [x] Filtre anti-bruit (`PAROLE_MIN`) contre les bruits brefs qui déclenchaient l'enregistrement
- [x] Réponse vocale avec Piper (`fr_FR-siwis-medium`)
- [x] Wake word « Hey Jarvis » avec openWakeWord : veille → conversation → retour en veille après un silence
- [x] Gestion d'erreur (`try` / `except ConnectionError`) : prévient à voix haute si Ollama est injoignable, retire la question restée sans réponse et retourne en veille
- [x] Modèle plus léger : `qwen3:8b` (5,6 Go en mémoire, contre 15 Go pour `mistral-small3.2`), qualité équivalente à l'oral. Vitesse à mesurer sur CPU, dans la VM
- [x] Historique limité (`assistant/historique.py`) : anciens résultats de recherche retirés, plus anciens échanges supprimés au-delà de 7 000 caractères, historique vidé après 10 minutes d'inactivité (contexte de `qwen3:8b` : 4096 tokens)
- [x] `SYSTEM_PROMPT` réécrit : persona Jarvis, règles précises (longueur, relances, actions impossibles, informations inconnues, erreurs de transcription) + exemples de bonnes réponses (few-shot)
- [x] Nettoyage des réponses par le code (`assistant/text.py`) : emojis et markdown retirés, unités sans abréviation, nombres en toutes lettres (`num2words`), accords (« une heure », « un litre »)
- [ ] Relances encore trop fréquentes (« Je peux t'en dire plus si tu veux. ») : limite d'un modèle 8b
- [x] Tool calling : recherche web (`assistant/tools.py`, bibliothèque `ddgs`, 3 résultats titre + extrait), boucle d'outils dans `ask_llm()` avec liste blanche `OUTILS`
- [x] Recherche web : lecture du contenu de la première page lisible (menus filtrés, coupé à 2 500 caractères) en plus des extraits
- [x] Recherche forcée quand on dit « recherche sur le web… » (`prepare_search`)
- [x] Relance automatique quand le modèle annonce ou propose une recherche sans appeler l'outil (« je cherche… », « je peux chercher… »)
- [x] Lieu par défaut (Festubert) dans le prompt
- [x] Date et heure actuelles injectées dans le message système à chaque question (le modèle ne les connaît pas)
- [ ] Outils suivants : météo (Visual Crossing, clé dans `.env`), calculatrice, trafic (TomTom ou HERE) ; plus tard SearXNG auto-hébergé à la place de `ddgs`
- [ ] Migration sur Linux + Docker (d'abord dans une VM de test, puis sur le mini PC du homelab)
