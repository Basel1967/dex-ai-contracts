# ADR-0001: Contract toolchain

Status: Accepted / MSR-011 closed in SESSION 20

Use Python 3.12, GNU Make, and the official `python:3.12-slim-bookworm` base pinned to
`python@sha256:a116514e19457bcb7af7efe9c3dd0b9b71e85b317694e7882a1c52aa15a78134`.

GitHub Actions run `32662099462` resolved the registry digest, built the devcontainer successfully, completed repository
verification, and scanned the built image with Trivy 0.70.0. The security gate found zero fixable `HIGH` or `CRITICAL`
vulnerabilities. Seventy unfixed findings are retained as temporary residual risk under `SECURITY.md` and weekly rescans.

Publication promotion must reuse committed immutable inputs; silent floating-tag substitution remains forbidden.

