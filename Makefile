.PHONY: all bootstrap lint validate test fixtures conformance compatibility traceability generate verify-generated security evidence package registry-dry-run clean
PYTHON := python3
all: bootstrap lint validate test fixtures conformance compatibility traceability generate verify-generated security evidence package registry-dry-run
bootstrap:
	@$(PYTHON) -c "import sys; assert sys.version_info[:2] == (3,12), sys.version"
	@echo BOOTSTRAP_PASS
lint:
	@$(PYTHON) -m compileall -q tooling tests
	@$(PYTHON) -c "import json,pathlib; [json.loads(p.read_text()) for p in pathlib.Path('.').rglob('*.json')]"
	@echo LINT_PASS
validate:
	@$(PYTHON) tooling/validate/runner.py >/dev/null
	@echo VALIDATE_PASS_WITH_MSR_011_BLOCKER
test: conformance
fixtures:
	@$(PYTHON) tooling/session18_build.py
	@$(PYTHON) -c "import json,pathlib; fs=list(pathlib.Path('fixtures').rglob('*.json')); assert len(fs)>=47; [json.loads(p.read_text()) for p in fs]; print('FIXTURES_PASS',len(fs))"
conformance:
	@$(PYTHON) tooling/validate/runner.py
compatibility:
	@$(PYTHON) -c "import json; d=json.load(open('metadata/compatibility-declaration.json')); assert d['compatibility_mode']=='NOT_APPLICABLE_UNPUBLISHED_PREDECESSOR'; open('reports/compatibility-report.json','w').write(json.dumps(d,indent=2)+'\n'); print('COMPATIBILITY_NOT_APPLICABLE_UNPUBLISHED_PREDECESSOR')"
traceability:
	@$(PYTHON) tooling/validate/runner.py >/dev/null
	@echo TRACEABILITY_PASS_SEMANTIC_CLOSURE_SCOPE
generate:
	@mkdir -p generated/manifests
	@sha256sum schemas/events/event-envelope/1.0.0/schema.json > generated/manifests/schema.sha256
	@echo GENERATED_NON_NORMATIVE
verify-generated:
	@sha256sum -c generated/manifests/schema.sha256
evidence:
	@$(PYTHON) tooling/evidence/build.py
security:
	@$(PYTHON) tooling/validate/runner.py >/dev/null
	@! find . -type f \( -name '.env' -o -name 'id_rsa' \) | grep .
	@echo SECURITY_INTEGRITY_PASS_CONTAINER_SCAN_BLOCKED_MSR_011
package: evidence
	@test -f releases/out/dex-ai-contracts-0.2.0-session18.tar.gz
	@echo PACKAGE_PASS_UNPUBLISHED_CANDIDATE
registry-dry-run: evidence
	@$(PYTHON) -c "import json; d=json.load(open('evidence/latest/registry-publication-dry-run.json')); assert d['result']=='DENIED_BY_DESIGN' and d['open_p0']; print('REGISTRY_DRY_RUN_FAIL_CLOSED')"
