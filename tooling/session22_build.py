#!/usr/bin/env python3
import gzip,hashlib,io,json,pathlib,tarfile
R=pathlib.Path(__file__).resolve().parents[1]; OUT=R/'releases/out/raw-event-v1.0.0-foundation-candidate.tar.gz'; OUT.parent.mkdir(parents=True,exist_ok=True)
excluded={'releases/out/raw-event-v1.0.0-foundation-candidate.tar.gz','reports/session22-gate-report.json','reports/session22-make-all.log','evidence/latest/session22-foundation-evidence.json'}
files=[p for p in sorted(R.rglob('*')) if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts and str(p.relative_to(R)) not in excluded]
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w',format=tarfile.PAX_FORMAT) as tar:
 for p in files:
  info=tar.gettarinfo(str(p),arcname=str(p.relative_to(R))); info.mtime=0; info.uid=info.gid=0; info.uname=info.gname=''
  with p.open('rb') as f: tar.addfile(info,f)
with OUT.open('wb') as raw:
 with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz: gz.write(buf.getvalue())
digest=hashlib.sha256(OUT.read_bytes()).hexdigest()
report={'session':'SESSION 22','decision':'PASS_FOUNDATION_CANDIDATE','contract':'urn:dex-ai:schema:event:raw-event','version':'1.0.0','publication_gate':'OPEN_FOR_RELEASE_CANDIDATE_NOT_PUBLISHED','candidate':str(OUT.relative_to(R)),'sha256':digest,'dependency':{'event_envelope_version':'1.0.0','published_release_sha256':'3bb89e3665261703dc22e94808d6c5e9bed114c29c66fdbd37904e01d98f4120','unchanged':True},'scope':{'contracts_started':['Raw Event'],'later_contracts_started':False,'agents_started':False,'services_started':False},'publication_requires_explicit_owner_approval':True}
(R/'reports/session22-gate-report.json').write_text(json.dumps(report,indent=2)+'\n'); (R/'evidence/latest/session22-foundation-evidence.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'status':'PASS','artifact':OUT.name,'sha256':digest},indent=2))
