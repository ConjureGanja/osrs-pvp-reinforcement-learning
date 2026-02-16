# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OSRS PvP Reinforcement Learning — trains AI agents to play Old School RuneScape PvP combat (NH bridding) using PPO and self-play. The system connects a Python ML training pipeline to a Java game simulation server via TCP sockets.

## Repository Structure

- **pvp-ml/** — Python ML training system (PyTorch, Gymnasium, Ray)
- **simulation-rsps/ElvargServer/** — Java RSPS game server (Gradle, Netty)
- **contracts/environments/** — JSON environment contracts defining action/observation spaces (NhEnv, DharokEnv)
- **gui.py / web_gui.py** — GUI and web launcher interfaces
- **SETUP_WALKTHROUGH.md** — Complete step-by-step guide for running the entire project

## Build & Development Commands

### Python (pvp-ml/)

```bash
# Environment setup
conda env create -p ./env -f pvp-ml/environment.yml
conda activate ./env
pip install -e pvp-ml/
pip install "setuptools<81"  # Required: Ray 2.7.1 needs pkg_resources removed in setuptools 82+

# Run all pre-commit checks (black, isort, flake8, mypy)
cd pvp-ml && pre-commit run --all-files

# Type checking
cd pvp-ml && mypy pvp_ml test --config=setup.cfg

# Unit tests
cd pvp-ml && pytest test/unit/

# Integration tests (requires simulation server running)
cd pvp-ml && pytest test/integ/

# Run a single test
cd pvp-ml && pytest test/unit/util/test_schedule.py

# Console entry points (after pip install -e)
train          # Training orchestrator (run_train_job.py)
serve-api      # Model serving API (api.py)
eval           # Model evaluation
```

### Java (simulation-rsps/ElvargServer/)

```bash
# Build and run server
cd simulation-rsps/ElvargServer && ./gradlew run

# Build only
cd simulation-rsps/ElvargServer && ./gradlew build

# Format check (spotless with palantir-java-format)
cd simulation-rsps/ElvargServer && ./gradlew check

# Auto-fix formatting (also fixes CRLF line endings)
cd simulation-rsps/ElvargServer && ./gradlew spotlessApply
```

### Full Project Setup

```bash
python setup.py              # Automated setup (installs Java, Conda env, etc.)
python setup.py --cpu-only   # CPU-only (no CUDA)
python setup.py --check-only # Check prerequisites only
```

**Note**: The automated setup.py may fail on some systems. See manual steps in SETUP_WALKTHROUGH.md.

## Architecture

### Communication Flow
```
Python ML system <-> TCP Socket (port 7070) <-> Java Game Server (port 43595)
                                                        |
Model Serving API (port 9999) <-> Eval Bots ───────────┘
```

### Training Mode
- `pvp_ml/env/pvp_env.py` — Gymnasium environment that connects via TCP to the game server
- `pvp_ml/env/remote_env_connector.py` — Handles socket communication (JSON over TCP, newline-delimited)
- `pvp_ml/env/simulation.py` — `Simulation` class manages RSPS lifecycle via Gradle subprocess
- Java side: `com.github.naton1.rl.RemoteEnvironmentServer` receives connections and drives `RemoteEnvironmentPlayerBot`

### Eval/Play Mode
- `pvp_ml/api.py` — TCP server on port 9999, loads all `.zip` models from `pvp-ml/models/`, serves inference
- Java side: `com.github.naton1.rl.AgentBotLoader` spawns `AgentPlayerBot` instances that query the API each game tick
- `com.github.naton1.rl.PvpClient` — Java TCP client that sends obs/actionMasks to Python API, receives actions
- Wire protocol: JSON request `{"model": "GeneralizedNh", "obs": [...], "actionMasks": [...]}` → response `{"action": [...]}`

### ML Training Pipeline
- `pvp_ml/train.py` — Main training loop (PPO with autoregressive action heads)
- `pvp_ml/run_train_job.py` — Job orchestration (spawns RSPS server, training, TensorBoard)
- `pvp_ml/ppo/` — PPO algorithm implementation
- `pvp_ml/ppo/policy.py` — Policy network with autoregressive action heads (12 action heads for gear, prayer, movement, eating, special attack)
- `pvp_ml/callback/` — 20+ callbacks for self-play, checkpointing, Elo rating, evaluation
- `pvp_ml/config/` — YAML configs (core.yml is the base; others inherit via `defaults`)

### Training Presets
Configs in `pvp-ml/config/nh/`:

| Preset | Network | Envs | Batch | Purpose |
|--------|---------|------|-------|---------|
| `test.yml` | 64 units, 1 layer (128K params) | 10 | 64 | Quick validation |
| `baseline.yml` | 512 units, 2 layers (1.77M params) | 100 | 2048 | Full training |
| `core.yml` | 512 units, 2 layers | 100 | 2048 | Production base config |
| `pure-self-play.yml` | 512 units | 100 | 2048 | Self-play only |
| `human-like.yml` | 512 units | 100 | 2048 | Human-like behavior |
| `human-like-adversarial.yml` | 512 units | 100 | 2048 | Exploit human-like opponents |

### Java Game Server
- Base RSPS (Elvarg) with RL plugin at `com.github.naton1.rl.ReinforcementLearningPlugin`
- Combat simulation in `com.elvarg.game.content.combat/`
- Environment contracts loaded from `contracts/environments/` define observation/action spaces
- `com.github.naton1.rl.EnvConfig` — reads all environment variables for server configuration
- `com.github.naton1.rl.env.nh.NhEnvironmentDescriptor` — defines NH observation/action encoding

### Pre-trained Models (pvp-ml/models/)
| Model | Parameters | Training Steps | Elo |
|-------|-----------|---------------|-----|
| `FineTunedNh.zip` | 1,774,985 | 238,080,000 | ~1620 |
| `GeneralizedNh.zip` | 1,774,985 | 161,792,000 | ~1590 |

## Running the Project

### Port Map
| Port | Service | Purpose |
|------|---------|---------|
| 43595 | RSPS Game Server | Game client connections |
| 7070 | Remote Env API | Python↔Java training communication |
| 9999 | Model Serving API | Inference for eval bots |
| 6006 | TensorBoard | Training metrics dashboard |

### Training
```bash
conda activate ./pvp-ml/env
cd pvp-ml
python -m pvp_ml.run_train_job cleanup --name all
python -m pvp_ml.run_train_job train --preset Test --id 0 --wait --log
# TensorBoard: http://localhost:6006
# Model checkpoints: pvp-ml/experiments/Test/models/
```

### Playing Against AI (Eval Mode)
```bash
# Terminal 1: API server
conda activate ./pvp-ml/env && cd pvp-ml && serve-api --device cpu

# Terminal 2: RSPS in eval mode
conda activate ./pvp-ml/env && cd simulation-rsps/ElvargServer
TRAIN=false RUN_EVAL_BOTS=true SYNC_TRAINING=false SHOW_ENV_DEBUGGER=false \
PREDICTION_API_HOST=localhost PREDICTION_API_PORT=9999 \
./gradlew run --no-daemon

# Terminal 3 (Windows): Game client — log in, walk to Wilderness, attack NhAgent bots
```

### Environment Variables (Java Server)
| Variable | Default | Purpose |
|----------|---------|---------|
| `TRAIN` | `true` | Enable RemoteEnvironmentServer for Python training |
| `RUN_EVAL_BOTS` | `true` | Spawn AI agent bots and scripted baselines |
| `SYNC_TRAINING` | `true` | Sync game ticks with trainer (false for real-time) |
| `TICK_RATE` | `600` | Game tick rate in ms (1 for max speed training) |
| `PREDICTION_API_HOST` | `localhost` | API server hostname |
| `PREDICTION_API_PORT` | `9999` | API server port |
| `GAME_PORT` | `43595` | Game client connection port |
| `REMOTE_ENV_PORT` | `7070` | Python training environment port |
| `SHOW_ENV_DEBUGGER` | `true` | Show environment debugger window |

### In-Game Commands
```
::enableagent env=nh model=GeneralizedNh stackFrames=1 deterministic=false
::disableagent
```

### Shutdown
```bash
lsof -ti :43595 -ti :7070 -ti :9999 -ti :6006 | sort -u | xargs -r kill
```

## WSL2-Specific Issues

**These are critical if developing on Windows + WSL2:**

- **CRLF line endings**: gradlew and Java sources may have `\r\n`. Fix gradlew: `tr -d '\r' < gradlew > /tmp/fix && cp /tmp/fix gradlew && chmod +x gradlew`. Fix Java: `./gradlew spotlessApply`
- **gradlew permissions**: Run `chmod +x simulation-rsps/ElvargServer/gradlew`
- **WSL2 networking**: Windows apps can't always reach WSL via `localhost`. Use WSL2 IP (`hostname -I`) in game client's `Configuration.java`
- **sed -i failures**: `sed -i` can fail silently on Windows filesystem. Use `tr` + temp file + `cp` instead
- **Slow filesystem**: Conda env creation and Gradle builds are slow on `/mnt/c/` (Windows filesystem via 9P)
- **Conda TOS**: Must accept before first env create: `conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main`

## Known Bugs

- **`queue.Empty` in run_train_job.py**: The orchestrator crashes in `propagate_logs()` but training/RSPS/TensorBoard continue running independently. Harmless.
- **`CANT_ATTACK_IN_AREA`**: Intermittent game simulation bug where a bot spawns outside the valid combat area. Causes training to crash. Restart training to recover.
- **setuptools compatibility**: Ray 2.7.1 needs `pkg_resources` which was removed in setuptools 82+. Fix: `pip install "setuptools<81"`

## Game Client (External)

The Elvarg game client is at https://github.com/RSPSApp/elvarg-rsps (ElvargClient directory). To use with Java 21+:
1. Remove unused `import jdk.nashorn.internal.runtime.regexp.joni.Config;` from `Slider.java`
2. Set `ENABLE_DISCORD_OAUTH_LOGIN = false` in `Configuration.java`
3. Set `SERVER_ADDRESS` to WSL2 IP in `Configuration.java` (if running server in WSL2)

A RuneLite plugin for live OSRS was developed but intentionally withheld from the repo to prevent misuse.

## Key Configuration

- **Python linting**: `pvp-ml/setup.cfg` — black (line-length 120), isort, flake8, mypy
- **Java formatting**: Spotless via Gradle (palantir-java-format), targets `com.github.naton1.rl/**/*.java`
- **CI**: `.github/workflows/test.yml` — runs pre-commit, mypy, gradle check, pytest
- **Pre-commit**: `pvp-ml/.pre-commit-config.yaml`

## Code Style Notes

- Python line length: 120 characters
- Python formatting: black + isort
- Java formatting: palantir-java-format via spotless
- Type hints used throughout Python code; mypy strict mode
