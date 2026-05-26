# Bunker
> Orchestrator — the single source of truth. Services report to it, it commands them back.

### RIGHT NOW (DEV):
- [ ] normalize JSON returns and make a standardized stdout system in services/agent.

### Now
- [ ] Build a proper Event Router
- [ ] Add outbound call function (so Bot can trigger services)
- [ ] Run Bot + Bunker together in one process

### Soon
- [ ] Add Bunker DB
  - [ ] Move chapter-checking logic into Bunker

---

# Services / Shared
- [ ] Replace `requests` with async alternative (`httpx`)

### Berserk Checker
- [ ] Local rate limiting (to not anger the Gods of webscraping)

### Pods Connect
- [ ] Add reconnect feature (disconnect+connect)
