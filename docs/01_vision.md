> Because software is to make a better life, not complicate it.

I see Bunker as a project of my life, at least right now. It's designed for me and by me, and will improve with me.

Structure:
┌ Bunker
├ Agent
├ Services
└ UI

# The Bunker (Orchestrator)

The main hub, through it goes everything. It sees everything, it commands everything, it logs everything. 

The main concentration of logic is located here: event-routing, timing services, evaluating etc.

## Database

Its DB is needed, to act as a single act of truth: ensures context and makes event-routing possible.

# The Agent

Local "connector" of Bunker and services. It handles mainly launching services and taking the info back to Bunker.

# Services

Designed to be dumb workers, they only complete their goal and print out JSON with a suitable return code.

# UI

Right now it's a Telegram bot, but I plan to add others, mainly:
 - digital environment integration (Linux)
 - website
