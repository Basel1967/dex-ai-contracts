.PHONY: all bootstrap lint envelope raw traceability security generate verify-generated package
PYTHON := python3
all: bootstrap lint envelope raw traceability security generate verify-generated package
bootstrap:
	@$(PYTHON) -c "import sys; assert sys.version_info[:2] == (3,12), sys.version"
	@echo BOOTSTRAP_PASS
lint:
	@$(PYTHON) -m compileall -q tooling tests
	@$(PYTHON) -c "import json,pathlib; [json.loads(p.read_text()) for p in pathlib.Path('.').rglob('*.json')]"
	@echo LINT_PASS
envelope:
	@$(PYTHON) tooling/validate/runner.py
raw:
	@$(PYTHON) tooling/validate/raw_event_runner.py
traceability:
	@test -f specs/contracts/events/raw-event/v1.md
	@test -f schemas/events/raw-event/1.0.0/schema.json
	@test -f metadata/raw-event-artifact-metadata.json
	@echo TRACEABILITY_PASS
security:
	@! find . -type f \( -name '.env' -o -name 'id_rsa' \) | grep .
	@$(PYTHON) -c "import hashlib,pathlib; p=pathlib.Path('releases/out/event-envelope-v1.0.0.tar.gz'); assert hashlib.sha256(p.read_bytes()).hexdigest()=='3bb89e3665261703dc22e94808d6c5e9bed114c29c66fdbd37904e01d98f4120'"
	@echo SECURITY_AND_IMMUTABILITY_PASS
generate:
	@mkdir -p generated/manifests
	@sha256sum schemas/events/event-envelope/1.0.0/schema.json schemas/events/raw-event/1.0.0/schema.json > generated/manifests/session22-schemas.sha256
	@echo GENERATED_NON_NORMATIVE
verify-generated:
	@sha256sum -c generated/manifests/session22-schemas.sha256
package:
	@$(PYTHON) tooling/session22_build.py
