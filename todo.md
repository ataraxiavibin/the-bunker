# Bunker
> Orchestrator — the single source of truth. Services report to it, it commands them back.

### RIGHT NOW (DEV):
- [ ] normalize JSON returns and make a standardized stdout system in services/agent.
  - [ ] it became kinda hard to keep it all in head. probably make a docs directory.

### Now
- [ ] Build a proper Event Router
- [ ] Add outbound call function (so Bot can trigger services)
- [ ] Run Bot + Bunker together in one process

### Soon
- [ ] Add Bunker DB
  - [ ] Move chapter-checking logic into Bunker

### Ideal
- [ ] Add automatic scanning of actions from local services (Agent)

---

# Services / Shared
- [ ] Replace `requests` with async alternative (`httpx`)

### Berserk Checker
- [ ] Local rate limiting (to not anger the Gods of webscraping)
- [ ] Track amount of days checking for a new chapter *(WHEN BUNKER WILL HANDLE LOGIC)*

### Pods Connect
- [ ] Add reconnect feature (disconnect+connect)
