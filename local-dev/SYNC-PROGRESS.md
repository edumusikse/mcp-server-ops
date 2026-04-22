# EduMusik Production → Local Sync Progress

## Goal
Full production mirror of server (178.104.32.37) into local OrbStack containers.

## Status Legend
- [ ] Not started
- [~] In progress
- [x] Done
- [!] Failed / needs attention

## Production Container Names (confirmed)
- Nextcloud app:   nextcloud-app-xogs4skwogkk8o40gkg8gs8g
- Nextcloud db:    nextcloud-db-xogs4skwogkk8o40gkg8gs8g
- Nextcloud redis: nextcloud-redis-xogs4skwogkk8o40gkg8gs8g
- Nextcloud cron:  nextcloud-cron-xogs4skwogkk8o40gkg8gs8g
- Vikunja app:     vikunja-jk448cwk4cwckokgscco88s4
- Vikunja db:      postgresql-jk448cwk4cwckokgscco88s4
- n8n app:         n8n-app-ps0cwo048sskc8wskow4gs4w
- n8n db:          n8n-db-ps0cwo048sskc8wskow4gs4w
- Kimai app:       kimai-vw00k0cw48c8swso840kg8cs
- Kimai db:        mysql-vw00k0cw48c8swso840kg8cs

## Step 1 — Find correct container names on server
- [x] Done — recorded above

## Step 2 — Database Dumps (on server → /tmp/db-dumps/)
- [x] nextcloud (postgres)
- [x] vikunja (postgres)
- [x] n8n (postgres)
- [x] kimai (mysql)

## Step 3 — Copy dumps to Mac (~/Documents/vs-code/local-dev/db-dumps/)
- [x] nextcloud.sql.gz
- [x] vikunja.sql.gz
- [x] n8n.sql.gz
- [x] kimai.sql.gz

## Step 4 — Restore into local containers
- [ ] nextcloud
- [ ] vikunja
- [ ] n8n
- [ ] kimai

## Step 5 — Nextcloud files volume
- [ ] Tar files volume on server
- [ ] Copy to Mac
- [ ] Restore into local nextcloud volume

## Notes
<!-- Record errors and anything else here -->

