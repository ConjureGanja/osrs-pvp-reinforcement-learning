# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OSRS PvP Reinforcement Learning — trains AI agents to play Old School RuneScape PvP combat using PPO and self-play. The system connects a Python ML training pipeline to a Java game simulation server via TCP sockets.

## Repository Structure

- **pvp-ml/** — Python ML training system (PyTorch, Gymnasium, Ray)
- **simulation-rsps/ElvargServer/** — Java RSPS game server (Gradle, Netty)
- **contracts/environments/** — JSON environment contracts defining action/observation spaces (NhEnv, DharokEnv)
- **gui.py / web_gui.py** — GUI and web launcher interfaces

## Build & Development Commands

### Python (pvp-ml/)

```bash
# Environment setup
conda env create -p ./env -f pvp-ml/environment.yml
conda activate ./env
pip install -e pvp-ml/

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
train          # Training orchestrator
serve-api      # Model serving API
eval           # Model evaluation
```

### Java (simulation-rsps/ElvargServer/)

```bash
# Build and run server
cd simulation-rsps/ElvargServer && ./gradlew run

# Build only
cd simulation-rsps/ElvargServer && ./gradlew build

# Format check (spotless)
cd simulation-rsps/ElvargServer && ./gradlew check
```

### Full Project Setup

```bash
python setup.py              # Automated setup (installs Java, Conda env, etc.)
python setup.py --cpu-only   # CPU-only (no CUDA)
python setup.py --check-only # Check prerequisites only
```

## Architecture

### Communication Flow
Python ML system <-> TCP Socket <-> Java Game Server

- `pvp_ml/env/pvp_env.py` — Gymnasium environment that connects via TCP to the game server
- `pvp_ml/env/remote_env_connector.py` — Handles socket communication
- Java side: `com.github.naton1.rl.RemoteEnvironmentServer` receives connections and drives `RemoteEnvironmentPlayerBot`

### ML Training Pipeline
- `pvp_ml/train.py` — Main training loop
- `pvp_ml/run_train_job.py` — Job orchestration (spawns simulation server, manages lifecycle)
- `pvp_ml/ppo/` — PPO algorithm with autoregressive action heads
- `pvp_ml/callback/` — 20+ callbacks for self-play, checkpointing, Elo rating, evaluation
- `pvp_ml/config/` — YAML configs (core.yml is the base; others inherit via `defaults`)

### Training Modes
Configs in `pvp-ml/config/nh/` define training strategies: baseline, pure-self-play, prioritized-past-self-play, human-like, and adversarial variants.

### Java Game Server
- Base RSPS (Elvarg) with RL plugin at `com.github.naton1.rl.ReinforcementLearningPlugin`
- Combat simulation in `com.elvarg.game.content.combat/`
- Environment contracts loaded from `contracts/environments/` define observation/action spaces

## Key Configuration

- **Python linting**: `pvp-ml/setup.cfg` — black (line-length 120), isort, flake8, mypy
- **Java formatting**: Spotless via Gradle (google-java-format)
- **CI**: `.github/workflows/test.yml` — runs pre-commit, mypy, gradle check, pytest
- **Pre-commit**: `pvp-ml/.pre-commit-config.yaml`

## Code Style Notes

- Python line length: 120 characters
- Python formatting: black + isort
- Java formatting: google-java-format via spotless
- Type hints used throughout Python code; mypy strict mode
