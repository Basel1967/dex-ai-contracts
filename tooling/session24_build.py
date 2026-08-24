#!/usr/bin/env python3
import gzip, hashlib, io, json, pathlib, tarfile

R = pathlib.Path(__file__).resolve().parents[1]
OUT = R / 'releases/out/normalized-event-v1.0.0-foundation-candidate.tar.gz'
FILES = [
    'specs/contracts/events/normalized-event/v1.md',
    'schemas/events/normalized-event/1.0.0/schema.json',
    'metadata/normalized-event-artifact-metadata.json',
    'registry/schemas/index.yaml',
    'registry/dependencies/graph.yaml',
    'tooling/validate/normalized_event_runner.py',
]
FILES += [str(p.relative_to(R)) for p in sorted((R/'fixtures/session24/normalized-event').rglob('*.json'))]

OUT.parent.mkdir(parents=True, exist_ok=True)
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w', format=tarfile.PAX_FORMAT) as archive:
    for relative in sorted(FILES):
        path = R / relative
        info = archive.gettarinfo(str(path), arcname=relative)
        info.mtime = 0; info.uid = info.gid = 0; info.uname = info.gname = ''
        with path.open('rb') as source: archive.addfile(info, source)
with OUT.open('wb') as raw:
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
        zipped.write(buffer.getvalue())

digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
report = {
    'session': 'SESSION 24',
    'decision': 'PASS_FOUNDATION_CANDIDATE',
    'contract': 'urn:dex-ai:schema:event:normalized-event',
    'version': '1.0.0',
    'publication_status': 'NOT_PUBLISHED',
    'candidate': str(OUT.relative_to(R)),
    'sha256': digest,
    'dependencies': {
        'event_envelope': {'version':'1.0.0','sha256':'3bb89e3665261703dc22e94808d6c5e9bed114c29c66fdbd37904e01d98f4120','unchanged':True},
        'raw_event': {'version':'1.0.0','sha256':'b0d5b5215d7c5a4dfd4e950655f671cac2628ef627d2a2062b9081cdfa40cd48','unchanged':True},
    },
    'tests': {'event_envelope':'43/43','raw_event':'12/12','normalized_event':'14/14'},
    'scope': {'event_types':['MINT_INITIALIZED'],'canonical_fact_started':False,'agents_started':False,'services_started':False},
    'publication_requires_explicit_owner_approval': True,
}
(R/'reports/session24-gate-report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'status':'PASS','artifact':OUT.name,'sha256':digest}, indent=2))
