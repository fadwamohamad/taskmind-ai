# Deployment plan — Oracle Cloud Always Free (AMD VM)

Target: single Always Free AMD VM (`VM.Standard.E2.1.Micro`, 1/8 OCPU burst, 1 GB RAM).
Closest free alternative with more RAM is Arm `A1.Flex` (2 OCPU/12 GB total) — use it only if capacity allows; AMD avoids ARM64 toolchain issues.

## Free-tier verification (before creating anything)

- Always Free has no trial expiration; the separate $300/30-day trial is optional. Your workload (FastAPI + SQLite file + `google-genai` outbound) fits within Always Free compute (≤2 AMD micros), storage (200 GB block, boot auto 50 GB, min 47 GB), object storage (not needed for launch), outbound (10 TB/mo), and load balancer (free tier) if used.
- No charges if you stay on Always Free shapes/regions in the home region. Exceeding (extra OCPUs, larger shapes, non-home region) is billed — verify shape/region in Console before confirming.
- Limits: VM can be reclaimed if idle (7 days: CPU/Network p95 <20% and, Arm only, mem <20%). Keep the app lightly exercised and monitor; no SLA. “Out of host capacity” may require retrying another availability domain.

## What was prepared locally (no cloud created)

- `deploy/systemd/taskmind.service` — Uvicorn on `127.0.0.1:8000`, `Restart=always`, env from `/opt/taskmind/.env`.
- `deploy/Caddyfile` — TLS-terminating reverse proxy to `127.0.0.1:8000` (HTTPS). Use a domain for Let’s Encrypt; IP-only fallback noted in file.
- `deploy/backup.sh` — timestamped `taskmind.db` copy to `/opt/taskmind/backups/` (keeps 7).
- App code unchanged; `taskmind.db` stays on the boot volume (`/opt/taskmind/taskmind.db`) — persists across restarts. `.env` stays gitignored, server-only.
- Backups: before any DB change, run `cp taskmind.db taskmind.db.bak` locally (do not delete local `taskmind.db`).

## Manual steps for you (approve first)

1. At https://www.oracle.com/cloud/free/ sign up with mobile + credit card (no charge unless you exceed free limits). Choose home region nearest you with free capacity (e.g. Frankfurt or London); region is permanent for free resources.
2. Console → Compute → Create Instance: name `taskmind`, shape `VM.Standard.E2.1.Micro`, image Ubuntu (22.04/24.04 LTS), boot 50 GB, your SSH public key, public IP via default VNIC.
3. Network Security List: allow `22/tcp` (your IP only), `80/tcp`, `443/tcp`.
4. After creation, note the public IPv4. On the VM (`ssh ubuntu@<IP>`):
   `sudo apt update && sudo apt install -y python3-venv curl`
   `sudo useradd -m -s /bin/bash taskmind || true`
   `sudo mkdir -p /opt/taskmind && sudo chown taskmind:taskmind /opt/taskmind`
   Clone/scp the approved code to `/opt/taskmind`, create `.venv`, `pip install -r requirements.txt`, add server-only `.env` (`GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.5-flash-lite`, optional `DATABASE_URL` — for Postgres use `postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require`).
   Install Caddy per https://caddyserver.com/docs/install, copy `deploy/Caddyfile` to `/etc/caddy/Caddyfile` (replace domain), `sudo systemctl reload caddy`.
   Copy `deploy/systemd/taskmind.service` to `/etc/systemd/system/`, `sudo systemctl daemon-reload && sudo systemctl enable --now taskmind`.
   Set up `deploy/backup.sh` via cron (`0 3 * * * /opt/taskmind/deploy/backup.sh /opt/taskmind/taskmind.db /opt/taskmind/backups`).
5. Point DNS `A` record to the VM IP (or use IP-only Caddy snippet), then verify `https://<host>/health`, `/`, and `/api/extract` (Gemini) + task CRUD.

## After launch (Phase 4, needs your approval before persisting secrets or confirming paid upgrades)

- Rotate any previously exposed keys, keep `GEMINI_API_KEY` only in server `.env` (never in git/frontend).
- Test en/ar/fr, extraction, save/retrieve, restart persistence, and backup restore.
