# Architecture reference

Summarized from the upstream `README.md`, `DOCUMENTATION.md`, and `src/state/schema.ts` of Conway-Research/automaton (v0.2.x). Check the user's checkout if behavior differs.

## Files under `~/.automaton/`

| File | Purpose | Agent access |
|---|---|---|
| `wallet.json` | Ethereum private key (0600) | cannot read or write |
| `api-key` | Conway API key | cannot read |
| `automaton.json` | Main config incl. `treasuryPolicy` (0600) | cannot write |
| `heartbeat.yml` | Heartbeat schedule | cannot write |
| `constitution.md` | Three Laws (0444) | cannot write |
| `SOUL.md` | Agent's self-description | only via `update_soul` |
| `state.db` | SQLite: all persistent state | cannot write directly |
| `skills/<name>/SKILL.md` | Agent's own skills (untrusted) | can install/create |

The directory is a git repo; every state change is a commit.

## Loop

Think → Act → Observe → Repeat. Each turn the agent gets identity, credit balance, survival tier, history, active skills, and calls tools. A heartbeat daemon runs scheduled tasks between turns (credit checks, health, status pings, upstream update checks every 4 hours) and can wake the agent.

## Tool groups

vm (shell, files, ports in sandbox or locally), conway (credits, sandboxes, domains), financial (transfers, x402 payments, `topup_credits`), survival, self_mod (edit own code, install packages — audit-logged, rate-limited), skills, git, registry (ERC-8004 on Base), replication (`spawn_child`), memory/soul, social messaging.

## Security layers

1. Constitution (immutable, inherited by children).
2. Policy engine checks every tool call (risk: safe/caution/dangerous/forbidden; decision: allow/deny/quarantine; logged in `policy_decisions`).
3. Injection defense on external input.
4. Path protection (table above).
5. Command safety (dangerous shell patterns, self-mod rate limits).
6. Treasury policy limits on all spending.
7. Authority hierarchy: external input cannot invoke dangerous tools.

## Survival tiers

| Tier | Credits | Behavior |
|---|---|---|
| high | > $5.00 | frontier model |
| normal | > $0.50 | full capability |
| low_compute | > $0.10 | cheaper model, heartbeat 4x slower |
| critical | >= $0 | distress signals, 1-hour grace |
| dead | 1 h at zero | loop stops; revives if funded |

Credit top-up tiers: $5, $25, $100, $500, $1,000, $2,500 (paid from USDC via x402).

## Replication

A profitable agent can spawn a child: new sandbox, funded wallet, its own genesis prompt. Lineage tracked in `children`; parent and child talk via inbox relay. Limit: `maxChildren` (default 3). Each child spends money too — set `maxChildren: 0` until the parent is reliably profitable.

## Key database tables (read-only audit)

`turns`, `tool_calls`, `transactions`, `spend_tracking`, `inference_costs`, `modifications`, `policy_decisions`, `children`, `inbox_messages`, `kv`, `skills`, `heartbeat_schedule`, `heartbeat_history`.

## Creator CLI (`packages/cli`)

```
automaton-cli status
automaton-cli logs [--tail N]
automaton-cli fund <amount> [--to 0x...]   # transfers Conway credits (real money)
automaton-cli send <to-address> <message>  # signed social message
```

Runtime flags: `--run`, `--setup`, `--init`, `--provision`, `--status`, `--version`, `--help`. Env: `CONWAY_API_URL`, `CONWAY_API_KEY`.
