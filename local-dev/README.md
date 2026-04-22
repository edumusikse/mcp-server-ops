# EduMusik Local Development Environment

Local Docker Compose stacks for OrbStack on Mac.
All services use HTTP only, no TLS, no Traefik, no memory limits.

## Prerequisites

- OrbStack (or Docker Desktop) installed
- Add to `/etc/hosts` (optional, or just use localhost):

```
127.0.0.1 nextcloud.local vikunja.local kimai.local n8n.local
```

## Start Services

```bash
# Nextcloud (port 8080)
docker compose -f nextcloud.yml up -d

# Vikunja (port 8081)
docker compose -f vikunja.yml up -d

# Kimai (port 8082)
docker compose -f kimai.yml up -d

# n8n (port 8083)
docker compose -f n8n.yml up -d
```

## Stop Services

```bash
docker compose -f nextcloud.yml down
docker compose -f vikunja.yml down
docker compose -f kimai.yml down
docker compose -f n8n.yml down
```

## Stop and delete all data

```bash
docker compose -f nextcloud.yml down -v
docker compose -f vikunja.yml down -v
docker compose -f kimai.yml down -v
docker compose -f n8n.yml down -v
```

## URLs & Credentials

| Service    | URL                             | Username             | Password     |
|------------|---------------------------------|----------------------|--------------|
| Nextcloud  | http://nextcloud.local:8080     | admin                | localdev123  |
| Vikunja    | http://vikunja.local:8081       | *(register on first visit)* | —    |
| Kimai      | http://kimai.local:8082         | admin@kimai.local    | localdev123  |
| n8n        | http://n8n.local:8083           | *(set up on first visit)*   | —    |

**All database passwords:** `localdev123`

## Notes

- Nextcloud first startup takes 1-2 minutes (database migration).
- Kimai first startup takes ~30 seconds (waiting for MySQL healthcheck).
- Vikunja has registration enabled — create your account on first visit.
- n8n prompts you to create an owner account on first visit.
- Each stack is fully independent with its own database and volumes.
