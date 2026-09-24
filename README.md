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

_À venir — premier script : micro → faster-whisper → texte affiché._

## Pièges connus

- **`python3 --version` affiche 3.9 sur Mac** : c'est le Python d'Apple (`/usr/bin/python3`). Homebrew installe la 3.11 sous le nom `python3.11` → toujours créer le venv avec `python3.11 -m venv .venv`. Une fois le venv activé, `python` pointe bien sur la 3.11.
- **Autorisation micro sur macOS** : au premier enregistrement, macOS demande l'accès au micro pour le Terminal / VS Code. Si c'est refusé, l'enregistrement est silencieux et Whisper ne renvoie rien (à réactiver dans *Réglages Système → Confidentialité et sécurité → Micro*).
- **Format audio attendu par Whisper** : 16 000 Hz, mono, `float32`, tableau 1D (`sounddevice.rec()` renvoie un tableau `(N, 1)` → `.flatten()`).
- **Portabilité** : pas de chemins en dur ni de libs spécifiques à macOS, le code doit tourner tel quel sur Linux.

## Roadmap

- [x] Ollama + `mistral-small3.2` fonctionnels en local
- [x] Environnement Python 3.11 (venv)
- [ ] Installer faster-whisper + sounddevice
- [ ] Script micro → transcription
- [ ] Brancher Ollama sur la transcription
- [ ] Réponse vocale avec Piper
- [ ] Wake word avec openWakeWord
- [ ] Migration sur le serveur homelab (Linux + Docker)
