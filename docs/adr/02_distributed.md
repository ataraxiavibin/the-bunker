# Why?

Without being on every device that needs that, this would be an incomplete system; it would make no sense.

Being able to drop an agent and services and run them on some type of a different device is an architectural need.

This opens so many opportunities for automatization, it's really only limited by imagination.

# What?

I always planned this to be a distributed system: Bunker on some type of a home server, Agents running locally on every device, and services on these devices.

Based on this, there are several important points:
 - this is a closed system with strictly controlled payloads.
 - services don't need to be ideal. Their only goal is to do their stuff and print only json in stdout.
   - at the same time, they should be as useful as it's possible within their scope.
 - services (probably, not sure) tend to be the most "stable" part of a system, their code is written once, polished one or two times and for a long time -- this is all.
   - there are constants which are theoretically "bad", but in this light i think it's really ok. since right now I can't test the system in its actual distributed state, it's alright. this may be easy changed to local .env files for agent + services.
   - i just don't want to make my .env complete with service variables right now.
 - it's no "humanity-changing" project. it's built by me and for me. the standards for code are really only defined by me, to balance clean code, ease of development, architectural cleanness and expandability.

# In the End

System is built the way it is, because it needs to be expandable and distributed. Project follows YAGNI in services area.
