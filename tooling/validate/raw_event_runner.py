#!/usr/bin/env python3
import copy, datetime, hashlib, importlib.util, json, pathlib, re, sys
R=pathlib.Path(__file__).resolve().parents[2]; P=[]; F=[]
TS=re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$'); RAW=re.compile(r'^urn:dex-ai:raw:[0-9a-f]{64}$'); SHA=re.compile(r'^sha256:[0-9a-f]{64}$'); ATTEMPT=re.compile(r'^urn:dex-ai:collection-attempt:[0-9a-f]{32}$'); SAFE=re.compile(r'^(https://|wss://|urn:dex-ai:)[A-Za-z0-9._~:/#-]+$')
spec=importlib.util.spec_from_file_location('envelope_runner',R/'tooling/validate/runner.py'); env=importlib.util.module_from_spec(spec); spec.loader.exec_module(env)
def load(p): return json.loads((R/p).read_text())
def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def dt(v): return datetime.datetime.strptime(v,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
def check(n,c,d=''): (P if c else F).append({'test':n,'passed':bool(c),'detail':'' if c else d})
def errors(e):
 z=list(env.errors(e)); p=e.get('payload');
 if not isinstance(p,dict): return z+['raw-payload:not-object']
 req={'capture_method','request_or_subscription_ref','source_endpoint_or_stream','source_received_at','http_or_transport_metadata','raw_content_type','raw_payload_ref','raw_content_hash','collector_clock','collection_attempt_id','redaction_manifest'}; allowed=req|{'source_cursor_or_checkpoint'}
 z += ['missing:'+x for x in sorted(req-set(p))]; z += ['unknown:'+x for x in sorted(set(p)-allowed)]
 if e.get('event_stage')!='RAW': z.append('stage:not-raw')
 if p.get('capture_method') not in {'POLL','SUBSCRIPTION','WEBHOOK','REPLAY_READ','INTERNAL_EMIT'}: z.append('capture-method')
 if p.get('capture_method')!=e.get('provenance',{}).get('collection_method'): z.append('mismatch:capture_method')
 endpoint=p.get('source_endpoint_or_stream')
 if not isinstance(endpoint,str) or not SAFE.fullmatch(endpoint) or '@' in endpoint or re.search(r'[?&](token|sig|key|secret|credential|authorization|cookie)=',endpoint,re.I): z.append('unsafe:source_endpoint_or_stream')
 if p.get('raw_content_type') not in {'application/json','application/octet-stream'}: z.append('raw-content-type')
 if not RAW.fullmatch(str(p.get('raw_payload_ref',''))): z.append('raw-payload-ref')
 if not SHA.fullmatch(str(p.get('raw_content_hash',''))): z.append('raw-content-hash')
 rr=e.get('raw_ref',{})
 if p.get('raw_payload_ref')!=rr.get('artifact_id'): z.append('mismatch:raw_payload_ref')
 if p.get('raw_content_hash')!=rr.get('content_hash'): z.append('mismatch:raw_content_hash')
 try:
  if not TS.fullmatch(p['source_received_at']) or dt(p['source_received_at'])>dt(e['observed_at']): z.append('source-received-time')
 except Exception: z.append('source-received-time')
 c=p.get('collector_clock')
 if not isinstance(c,dict) or set(c)!={'clock_source','captured_at','uncertainty_ms'}: z.append('collector-clock')
 else:
  if c['clock_source'] not in {'SYSTEM_UTC','SOURCE_REPORTED','MONOTONIC_CORRELATED'}: z.append('clock-source')
  if not isinstance(c['uncertainty_ms'],int) or not 0<=c['uncertainty_ms']<=60000: z.append('clock-uncertainty')
  try:
   if not TS.fullmatch(c['captured_at']): z.append('clock-time')
   else: dt(c['captured_at'])
  except Exception: z.append('clock-time')
 if not ATTEMPT.fullmatch(str(p.get('collection_attempt_id',''))): z.append('collection-attempt-id')
 if not isinstance(p.get('redaction_manifest'),list) or len(p.get('redaction_manifest',[]))>64: z.append('redaction-manifest')
 m=p.get('http_or_transport_metadata')
 if m is not None and (not isinstance(m,dict) or set(m)!={'transport','status_code','content_encoding','message_id'}): z.append('transport-metadata')
 return sorted(set(z))
def mutate(b,m):
 o=copy.deepcopy(b)
 if 'remove' in m:
  a,k=m['remove'].split('.',1); o[a].pop(k,None)
 for path,v in m.get('replace',{}).items():
  a,k=path.split('.',1); o[a][k]=v
 return o
def main():
 s=load('schemas/events/raw-event/1.0.0/schema.json'); check('raw-schema-2020-12',s.get('$schema')=='https://json-schema.org/draft/2020-12/schema'); check('raw-schema-closed',s.get('additionalProperties') is False); check('raw-gate-open-after-verification',s.get('x-publication-status')=='OPEN_FOR_RELEASE_CANDIDATE_NOT_PUBLISHED')
 good=load('fixtures/session22/raw-event/valid/minimal.json'); check('raw-minimal-valid',not errors(good),','.join(errors(good))); check('raw-payload-digest-valid',good['payload_hash']=='sha256:'+hashlib.sha256(canon(good['payload'])).hexdigest())
 for p in sorted((R/'fixtures/session22/raw-event/invalid').glob('*.json')):
  d=json.loads(p.read_text()); er=errors(mutate(good,d['mutation'])); check('raw-reject-'+p.stem,d['expected_error'] in er,','.join(er))
 altered=copy.deepcopy(good); altered['payload']['source_cursor_or_checkpoint']='slot:2'; check('raw-tampering-detected','integrity-mismatch' in errors(altered))
 reg=load('registry/schemas/index.yaml'); graph=load('registry/dependencies/graph.yaml'); check('event-envelope-registry-published',reg['artifacts'][0]['publication']=='PUBLISHED'); check('raw-dependency-retained',any(x.get('artifact')=='urn:dex-ai:schema:event:raw-event:1.0.0' and x.get('depends_on')=='urn:dex-ai:schema:event:event-envelope:1.0.0' and x.get('dependency_status')=='PUBLISHED' for x in graph['entries']))
 release=R/'releases/out/event-envelope-v1.0.0.tar.gz'; check('published-envelope-digest-unchanged',hashlib.sha256(release.read_bytes()).hexdigest()=='3bb89e3665261703dc22e94808d6c5e9bed114c29c66fdbd37904e01d98f4120')
 status='PASS' if not F else 'FAIL'; report={'session':'SESSION 24 regression','contract':'Raw Event 1.0.0','status':status,'passed':len(P),'failed':len(F),'results':P+F}; (R/'reports/session24-raw-event-regression-report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'status':status,'passed':len(P),'failed':len(F)},indent=2)); return 0 if not F else 1
if __name__=='__main__': sys.exit(main())
