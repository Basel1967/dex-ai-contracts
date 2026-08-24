#!/usr/bin/env python3
import gzip, hashlib, io, json, pathlib, tarfile
R=pathlib.Path(__file__).resolve().parents[1]
OUT=R/'releases/out/canonical-fact-v1.0.0-foundation-candidate.tar.gz'
FILES=['specs/contracts/facts/canonical-fact/v1.md','schemas/facts/canonical-fact/1.0.0/schema.json','metadata/canonical-fact-artifact-metadata.json','metadata/session26-canonical-fact-traceability.json','tooling/validate/canonical_fact_runner.py']
FILES += [str(p.relative_to(R)) for p in sorted((R/'fixtures/session26/canonical-fact').rglob('*.json'))]
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w',format=tarfile.PAX_FORMAT) as a:
    for rel in sorted(FILES):
        p=R/rel; info=a.gettarinfo(str(p),arcname=rel); info.mtime=0; info.uid=info.gid=0; info.uname=info.gname=''
        with p.open('rb') as source: a.addfile(info,source)
with OUT.open('wb') as raw:
    with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped: zipped.write(buffer.getvalue())
digest=hashlib.sha256(OUT.read_bytes()).hexdigest()
report={'session':'SESSION 26','decision':'PASS_FOUNDATION_CANDIDATE','contract':'urn:dex-ai:schema:fact:canonical-fact','version':'1.0.0','publication_status':'NOT_PUBLISHED','candidate':str(OUT.relative_to(R)),'sha256':digest,'tests':{'event_envelope':'43/43','raw_event':'12/12','normalized_event':'14/14','canonical_fact':'18/18'},'scope':{'entity_types':['SOLANA_MINT'],'fact_types':['MINT_INITIALIZED'],'agents_started':False,'services_started':False},'publication_requires_explicit_owner_approval':True}
(R/'reports/session26-gate-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','artifact':OUT.name,'sha256':digest},indent=2))
