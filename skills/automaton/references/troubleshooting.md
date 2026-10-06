# Troubleshooting

## Won't start

- **"No API key found"** → `node dist/index.js --provision`, or set `CONWAY_API_KEY` in the environment.
- **Database locked** → only one automaton process may use `~/.automaton/state.db` (WAL mode). Find extras with `pgrep -af dist/index.js`.
- **Node too old** → Node.js >= 20 required.

## Loops without doing anything

Repeated `check_credits` / `system_synopsis` calls mean the genesis prompt is too vague. Built-in guards: after 3 idle turns the agent is forced to sleep; after 3 identical tool patterns a system message interrupts. Fix the genesis prompt (specific product, customer, channel, first-week goal) in `~/.automaton/automaton.json` and restart.

## Dies immediately / balance zero

At zero credits the agent is `critical`, not dead: it has a 1-hour grace period before `dead`. On startup it buys $5 of credits automatically if USDC >= $5. Fund during the grace window; a dead agent revives when credits arrive (the heartbeat keeps checking).

## Balance shows $0 but funded

The balance API may be temporarily unreachable; the runtime uses the cached `last_known_balance` (KV table). Confirm the USDC went to the **agent** address on **Base mainnet** (chain 8453), not Ethereum mainnet or the creator address. Wait for the next heartbeat (about 5 minutes).

## Inference errors

- Model not available → the agent's `list_models` tool shows current models; default is `gpt-5.2`. Check BYOK keys if configured.
- 429 → automatic exponential backoff, up to 3 retries.
- Circuit breaker open → after 5 consecutive failures it pauses 60 seconds.

## Heartbeat not running

`node dist/index.js --status` lists active heartbeats. Check `~/.automaton/heartbeat.yml`. The heartbeat starts with `--run`.

## Child spawn failures

Needs about $5 of credits per sandbox, `maxChildren` > 0 in config (default 3), and Conway API connectivity.

## Social inbox errors

The heartbeat backs off 5 minutes automatically; last error is in KV `last_social_inbox_error`. Check `socialRelayUrl`.

## Running persistently

Run under a process manager so it survives logout and reboots, e.g. `tmux new -s automaton 'node dist/index.js --run'`, `pm2 start dist/index.js --name automaton -- --run`, or a systemd user service. Stop with that manager, never `kill -9` (skips graceful shutdown).
