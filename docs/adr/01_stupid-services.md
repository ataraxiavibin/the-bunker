# Why?

I always wanted an easily expandable, reliable and smart system. The old architecture was built using the right words and completely wrong code.

Services would know a about contracts, namely they would send their service name, status and "payload" dictionary, which previously led to monstrosities in Bunker such as `agent_data["payload"]["stdout"]["payload"]`. They would also handle logic of either printing only json (for Agent) or "normal" human-readable output.

It was also not clear, how do I clearly differentiate status. Because there was two statuses: one inside the Reply, the other inside `["stdout"]["payload"]`! Tell me about bad decisions.

It even lead to me noticing, that in bot I get "all-good" answer, while the service actually just crashed cuz of a syntax error i made. I don't remember exactly how it happened, but man it was dumb.

# What?

So, to untangle this, I started with a question: 
 - how can I 100% distinguish result of Reply? 

I mean, before it was possible. I was just to lazy and too perfectionist to solve this in a already deeply flawed architecture.

So, the first change was: change the models. This is a matter of other place in docs/ (for example, contracts.md or my journal), so I'm not gonna explain it here.

Once the models were changed to their correspondible Ok/Error versions using Union discriminated by "status", I started on thinking: 
 - what really are my services?

They are stupid. That means:
 1. Do your thing, print and die. *it is enough right now, but that may change when/if some services will run as daemons in background*
 2. Die with the right exit code.
 3. Do not use stdout for anything other than json.
 4. In case of an error, print to stderr. 
 5. Do not use any dependencies from shared/, be fully independent.

Those limitations mean that something else is going to overtake some of their old responsibilities. Which is fine and expectable.

Which also means that Agent must be more powerful:
 1. Depending on exit code, get the status.
 2. Construct Event/Reply Ok/Error fully, with stdout of a service as payload.

I want to still have to opportunity to run services manually from my terminal, and not reading JSON as an output. That's why Event was even created, that was the first implementation of communication between services and Bunker ever.

 3. If arguments (`agent.py run {service} {action} (--text) [--reply-to ...]`) provided, use them to run the service and construct Event/Reply.
    - --reply-to is just a vision; it will be some time before I do implement that. *i do not like the idea of bunker directly calling TelegramAPI*

# Questions not answered

1.
When all is done, status will be fairly accurately determined. It's enough for MVP, but what about reason? There is such a field in the models.

I have no idea, really. There is exit codes and I could do that, but it's... i don't like that idea, you know?

2.
Logging in services without trashing stdout/err. How do I do that cleanly?

# In the End

"Stupid services" solves a couple of design problems I had:
  - language-agnosticism    -- services don't use shared/ modules.
  - expandability           -- services don't care about anything but their own business-logic.
  - system clarity          -- easier contracts; distinct Ok/Error models
  - new features            -- timestamp + duration_ms in Reply/event models.
