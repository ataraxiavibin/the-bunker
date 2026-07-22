Project Bunker: my personal Automation Hub.

The vision is to make a system that connects and automates the gap between software and hardware in my everyday life. Because software is to make a better life, not complicate it.

Based on an event-driven architecture, Bunker acts as the central nervous system; the microservices follow "do one thing and do it well" philosophy.

# System architecture & Call lifecycle

Right now Bunker follows a strict architecture: Client/UI -> Bunker -> Agent -> Service:

    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │  Client/UI   │ ──(1)──>│    Bunker    │ ──(2)──>│    Agent     │ ──(3)──>│   Service    │
    │ (Telegram)   │<──(6)───│(Orchestrator)│<──(5)───│(Local Runner)│<──(4)───│ (Subprocess) │
    └──────────────┘         └──────────────┘         └──────────────┘         └──────────────┘
      Register/Call           Route & Normalise       Execute & Parse          Execute & Output

There are three main statuses:
 - **ok**: everything went well
 - **error**: expected error on a service side
 - **fatal**: unexpected error, system integrity compromised

# Features

Currently, the project is in its early stages, but a lot is already done!

## The Orchestrator (Bunker)

- **FastAPI Hub**: fast, asynchronous orchestrator.
- **strict Pydantic contracts**: enforces validated models (`Call`, `Event`, `Reply` etc.) using discriminated unions.
- **registration**: registers every `Intent` from UI, enabling end-to-end tracing.
- **end-to-end tracing**: every request can be tracked using the id.
- **token auth**: all internal endpoints are secured with constant time verification.

## Agent

- **local-first**: designed to run local services on different devices and pass the execution results to Bunker.
- **language-agnostic**: uses `asyncio.create_subprocess_exec` to launch files of any programming language: Python, Rust, Bash, C - just make sure it spits json out.
- **CLI Mode**: manual service execution from terminal `python -m agent run <service> <action> [-t]` with automatic Event reporting.

## Services

- **zero shared dependencies**: services operate independently without importing Bunker shared libraries.
- **simple architecture**: services can do their thing, print the results in json and die with the right exit code.
- **first services**: a Berserk manga new chapter checker and a simple AirPods (actually, any Bluetooth device) toggler.

## UI

- **telegram TUI**: bot built with aiogram 3; custom terminal-styled interface.
- **intents**: commands like `/chapter` or `/pods connect` send real Intents to Bunker and initiate Calls.
- **automated diagnostics**: runs system health checks if a request fails.

# Journal

- **ADRs**: i try to keep important things there.
- **journal**: my thoughts, my way of getting things done.

# Setup

Project Bunker uses hybrid deployment:
- bunker & bot run inside Docker containers;
- agent runs directly on the host machine.

Requires a Linux machine, Docker & Docker Compose, Python 3.14+.

1. clone the repository
2. fill in `.env` based on `.env.example`
3. `pip install -r requirements.txt` (required for Agent, but not all of it)
4. `./run.sh` (`&>/dev/null &` recommended) - right now this script uses hot-reloading, because project is still in development.

# License

This project is free software licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
