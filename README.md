## guide
- set variables in `config.py` and `.env` (api keys, proxy, ...)
- set `PRIVATE_ROUTER_URL` + `PRIVATE_ROUTER_TOKEN` (Telegram fetch goes through **private-router**; no local Telethon session)
- ensure private-router is healthy: `curl -s http://127.0.0.1:3010/health`
- set telegram channel username in `playlistify.py` without `@`
- run the `playlistify.py`

### list of created channels:
https://t.me/Playlistify_Channel
