# EduMusik Local Dev — Production Sync Log

## Status Key
- [ ] Not started
- [~] In progress
- [x] Complete
- [!] Failed / needs retry

## Goal
Full production mirror of EduMusik server (178.104.32.37) to local OrbStack environment.

---

## Container Names on Server (confirmed)
- nextcloud DB: nextcloud-db-xogs4skwogkk8o40gkg8gs8g
- n8n DB:       n8n-db-ps0cwo048sskc8wskow4gs4w
- kimai DB:     mysql-vw00k0cw48c8swso840kg8cs (root password via MYSQL_ROOT_PASSWORD env)
- vikunja DB:   postgresql-jk448cwk4cwckokgscco88s4 (user: 5Dxd6byzJJTdaaHY)

## Step 1 — Find correct container names on server
- [x] Complete

## Step 2 — Dump databases on server to /tmp/db-dumps/
- [x] nextcloud.sql.gz
- [x] vikunja.sql.gz
- [x] n8n.sql.gz
- [x] kimai.sql.gz

## Step 3 — Copy dumps to Mac
- [x] ~/Documents/vs-code/local-dev/dumps/nextcloud.sql.gz (1.3MB)
- [x] ~/Documents/vs-code/local-dev/dumps/vikunja.sql.gz (8.3KB)
- [x] ~/Documents/vs-code/local-dev/dumps/n8n.sql.gz (28KB)
- [x] ~/Documents/vs-code/local-dev/dumps/kimai.sql.gz (15KB)

## Step 4 — Restore into local containers
- [x] nextcloud — stopped app, dropped/recreated DB, restored, restarted
- [x] vikunja — dropped/recreated DB, restored
- [x] n8n — stopped app, dropped/recreated DB, restored, restarted
- [x] kimai — stopped app, dropped/recreated DB, restored, restarted

## Step 5 — Nextcloud files volume
- [ ] Tar up /var/www/html on server
- [ ] Copy to Mac
- [ ] Restore into nextcloud-local_nextcloud-data volume

## Step 6 — Verify
- [ ] Nextcloud http://localhost:8080 — data visible
- [ ] Vikunja http://localhost:8081 — projects visible
- [ ] Kimai http://localhost:8082 — timesheets visible
- [ ] n8n http://localhost:8083 — workflows visible

---
## Notes
- vikunja DB user on server is 5Dxd6byzJJTdaaHY (Coolify-generated)
- n8n and kimai need app stopped before DB restore (active connections)
