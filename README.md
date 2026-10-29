# Birja

## The idea

A website where you practice investing with **virtual money at real market prices**.

You start with a virtual balance of dollars and can buy and sell:

- company stocks
- gold
- bonds
- cryptocurrencies
- currencies from different countries

Prices come from real markets and update live. If you buy gold today and gold goes up next week, your virtual portfolio goes up too. The money just isn't real.

## Why

Most of us know too little about investing, and the usual way to learn it is to lose real money. This removes that risk. You can try things, make mistakes, and see what actually happens, without paying for the lesson.

## How it works for you

1. Sign up and get your starting virtual balance.
2. Pick assets and decide how much to buy.
3. Check in whenever you like. You'll see:
   - how much your portfolio is worth now
   - your total profit or loss
   - which investments are doing well and which aren't
   - how your portfolio's value has changed over time

There's no time travel or hindsight. Like real investing, you make a decision today and find out in the weeks and months after.

## Run locally

Prerequisites: Docker with Compose v2+. uv and Node 24 are only needed to run lint and tests outside containers.

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:5173 and expect API, Database and Redis to show "Connected". For tests, lint and migrations see "Common commands" in [CLAUDE.md](CLAUDE.md).

CI runs on every PR into `develop`/`main`; the `ci-pass` check must be green before merging.

## AI development

Claude Code and Codex share the rules in [CLAUDE.md](CLAUDE.md) and the existing
GSD state in `.planning/`. Codex starts from [AGENTS.md](AGENTS.md); use
`$gsd-progress` to inspect the project. See [the Codex guide](docs/CODEX.md)
for skills, setup checks, and command equivalents.

## Deploying

Production runs at https://birja.nist.one. Deploy from `main` on the server with `/srv/birja/deploy/deploy.sh` (as root). Setup, rollback, certificate renewal and undo steps are in [deploy/RUNBOOK.md](deploy/RUNBOOK.md).
