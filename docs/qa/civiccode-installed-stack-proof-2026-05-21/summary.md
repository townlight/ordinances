# CivicCode Installed-Stack Proof - 2026-05-21

Status: PASS for Docker/PostgreSQL installed-stack smoke and backup/restore proof.

Successful run:

```powershell
$project='civiccode_product_completion_evidence3'
$env:CIVICCODE_PORT='18066'
docker compose -p $project up -d --build
bash -lc 'CIVICCODE_SMOKE_BASE_URL=http://127.0.0.1:18066 scripts/docker-demo-smoke.sh'
python scripts/check_docker_backup_restore_rehearsal.py --run-id civiccode-product-completion-evidence3-2026-05-21 --compose-project-name $project --strict
docker compose -p $project down -v
```

Evidence files:

- `docs/qa/civiccode-installed-stack-proof-2026-05-21/compose-up-3.log`
- `docs/qa/civiccode-installed-stack-proof-2026-05-21/docker-demo-smoke-3.log`
- `docs/qa/civiccode-installed-stack-proof-2026-05-21/backup-restore-3.log`
- `docs/qa/civiccode-installed-stack-proof-2026-05-21/api-3.log`
- `docs/qa/civiccode-installed-stack-proof-2026-05-21/compose-down-3.log`

Observed result:

- Compose build completed.
- PostgreSQL service became healthy.
- API service became healthy.
- Alembic ran CivicCore then CivicCode migrations through `civiccode_0011_semantic_search`.
- Public seeded lookup passed.
- Staff seeded workspace passed.
- `DOCKER-DEMO-SMOKE: PASSED`.
- Backup/restore rehearsal passed with `pg_dump`, temporary restore database creation, `pg_restore`, restored-table verification, and cleanup.
- `DOCKER-BACKUP-RESTORE-REHEARSAL: PASSED`.

Boundary:

This proves the active CivicCode branch can build and run under its Docker
Compose/PostgreSQL profile and preserve/restore the database. It does not yet
prove CivicSuite installer/module-selection integration or independent audit
clearance.
