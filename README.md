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
| LLM | [Ollama](https://ollama.com) + `mistral-small3.2` | Génère la réponse, en local via `localhost:11434` |
| Text-to-Speech | [Piper](https://github.com/OHF-Voice/piper1-gpl) | Transforme la réponse en voix |
| Orchestration | Python 3.11 | Relie toutes les étapes |

## Prérequis

- **Python 3.11**
- **Ollama** installé, avec le modèle téléchargé :
  ```bash
  ollama pull mistral-small3.2
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
- [ ] Gestion d'erreur (`try` / `except`) : prévenir à voix haute si Ollama est injoignable
- [ ] Tester un modèle Ollama plus léger (`mistral-small3.2` pèse 15 Go, trop pour la VM de test et un mini PC modeste)
- [ ] Tool calling : d'abord une calculatrice (le LLM se trompe en calcul mental), puis météo (Open-Meteo) et trafic (TomTom ou HERE)
- [ ] Migration sur Linux + Docker (d'abord dans une VM de test, puis sur le mini PC du homelab)
