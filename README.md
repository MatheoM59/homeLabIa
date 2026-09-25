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
| Text-to-Speech | [Piper](https://github.com/rhasspy/piper) | Transforme la réponse en voix |
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

Boucle : écoute 5 s → transcription → réponse de l'IA (avec mémoire de la conversation). Un silence arrête l'assistant.

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
- **Portabilité** : pas de chemins en dur ni de libs spécifiques à macOS, le code doit tourner tel quel sur Linux.

## Roadmap

- [x] Ollama + `mistral-small3.2` fonctionnels en local
- [x] Environnement Python 3.11 (venv)
- [x] Installer faster-whisper + sounddevice
- [x] Script micro → transcription (`scripts/test_micro.py`)
- [x] Appel à Ollama avec consigne système + mémoire de conversation (`scripts/test_llm.py`)
- [x] Assembler le pipeline dans le package `assistant/` (micro → Whisper → Ollama)
- [x] Filtre VAD contre les hallucinations de Whisper sur le silence
- [ ] Détection de fin de parole (VAD) au lieu d'un enregistrement de durée fixe
- [ ] Réponse vocale avec Piper
- [ ] Wake word avec openWakeWord
- [ ] Migration sur le serveur homelab (Linux + Docker)
