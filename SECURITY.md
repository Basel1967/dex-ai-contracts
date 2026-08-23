# Security

PR CI is read-only with minimal permissions, has no production environment, secrets, credentials, registry write token,
wallet key, or production data. All publication commands are dry-run and deny `production`. Environment isolation is
fail-closed. Report vulnerabilities privately to the future named Security Owner (currently the project owner, Basel Atta).

## Container vulnerability gate

The devcontainer image is scanned with Trivy for `HIGH` and `CRITICAL` vulnerabilities after digest verification and a
successful Docker build. Any `HIGH` or `CRITICAL` vulnerability with a non-empty fixed version blocks the gate.

An unfixed `HIGH` or `CRITICAL` vulnerability may be accepted temporarily only as recorded residual risk. The full Trivy
report, the residual-risk subset, the resolved base digest, and the build log are retained as workflow evidence. The
workflow reruns weekly and on demand. A newly available fixed version converts the finding into a blocking failure.

Publication remains fail-closed until the successful SESSION 20 evidence is committed and MSR-011 is explicitly closed.
