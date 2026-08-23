# Security

PR CI is read-only with minimal permissions, has no production environment, secrets, credentials, registry write token,
wallet key, or production data. All publication commands are dry-run and deny `production`. Environment isolation is
fail-closed. Report vulnerabilities privately to the future named Security Owner (currently a publication blocker).
