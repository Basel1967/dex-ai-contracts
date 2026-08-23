# dex-ai-contracts

Foundation contract repository for DEX AI. This repository contains specifications, draft executable schemas,
synthetic fixtures, conformance tooling, traceability and release-candidate evidence. It contains no service,
agent, provider integration, production credential, trading, signing-wallet or fund-movement logic.

## Current gate

**PASS — Publication Gate OPEN.** Event Envelope semantic closure passed, all P0 missing-source items are closed,
and SESSION 20 verified an immutable devcontainer digest, a successful Docker build, repository conformance, and a
Trivy scan with zero fixable `HIGH` or `CRITICAL` vulnerabilities. Unfixed residual risk is documented and rescanned
weekly. See `decisions/missing-source-register.yaml` and `evidence/latest/session20-publication-gate.json`.

Opening the gate does not itself begin or implement any subsequent contract.

## Reproducible commands

`make all`

Python 3.12 is pinned by the digest-resolved devcontainer. Production credentials are neither required nor used.

