Project Bunker: my personal Automation Hub.

The vision is to make a system, that connects and automates the gap between software and hardware in my everyday life. Because software is to make a better life, not complicate it.

Based on an event-driven architecture, Bunker acts as the central nervous system; the microservices follow "do one thing and do it well" philosophy.

# Features

Currently, the project is in its early (really early) stages. Event routing is read-only, services can report to Bunker, but Bunker cannot yet call services; only two services at the moment.

## The Orchestrator (Bunker)

- **FastAPI hub**: acts as the single source of truth
- **Standardized event routing**: strict JSON payload structure (`source`, `status`, `payload`)

## Services 

- **Shared communication**: a shared module `transmitter.py` that any local script can use to report its status
- **First services**: a Berserk manga new chapter checker and a simple AirPods (actually, any Bluetooth device) toggler

## UI

- **Telegram Bot**: a simple aiogram bot to control the system from my phone.

# Setup

Requires a Linux machine.

1. Clone the repository
2. Fill in `.env` based on `.env.example`
3. `pip install -r requirements.txt`
4. `./run.sh` (`&>/dev/null &` recommended)

# License

This project is free software licensed under the GNU General Public License v3.0. See the (LICENSE)[LICENSE] file for details.
