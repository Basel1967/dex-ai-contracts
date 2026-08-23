# dex-ai-contracts

Foundation contract repository for DEX AI. This repository contains specifications, draft executable schemas,
synthetic fixtures, conformance tooling, traceability and release-candidate evidence. It contains no service,
agent, provider integration, production credential, trading, signing-wallet or fund-movement logic.

## Current gate

**CONDITIONAL PASS — repository bootstrap; FAIL-CLOSED for Event Envelope publication.** The schema is a
`Draft` candidate with technical Event Envelope semantics closed. Publication remains blocked solely by MSR-011: an independently verified immutable devcontainer base digest, build log and container security scan. See `decisions/missing-source-register.yaml`.

## Reproducible commands

`make all`

Python 3.12.13 is pinned. The toolchain uses only the Python standard library. Network access and credentials are
neither required nor used.
