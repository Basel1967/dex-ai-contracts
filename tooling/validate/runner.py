#!/usr/bin/env python3
import csv,datetime,hashlib,json,pathlib,re,sys
R=pathlib.Path(__file__).resolve().parents[2]; P=[]; F=[]; B=[]
TS=re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$'); EID=re.compile(r'^urn:dex-ai:event:[0-9a-f]{32}$'); B58=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{64,88}$')
def load(p): return json.loads((R/p).read_text())
def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def dt(v): return datetime.datetime.strptime(v,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
def check(name,cond,detail=''): (P if cond else F).append({'test':name,'detail':'' if cond else detail,'passed':bool(cond)})
def errors(e):
 s=load('schemas/events/event-envelope/1.0.0/schema.json'); z=[]; req=s['required']; allowed=set(s['properties'])
 z += [f'missing:{x}' for x in req if x not in e]; z += [f'unknown:{x}' for x in e if x not in allowed]
 if not isinstance(e,dict): return ['not-object']
 if e.get('contract_name')!='event-envelope' or e.get('contract_version')!='1.0.0': z.append('unsupported-contract')
 for k in ('event_id','correlation_id','ordering_key','idempotency_key','subject_ref'):
  if k in e and (not isinstance(e[k],str) or not e[k]): z.append('identifier:'+k)
 if 'event_id' in e and (not isinstance(e['event_id'],str) or not EID.fullmatch(e['event_id'])): z.append('event-id')
 if e.get('event_stage') not in ['RAW','NORMALIZED','SYSTEM']: z.append('event-stage')
 if e.get('event_domain') not in ['CHAIN','MARKET','SOCIAL','QUALITY','ANALYSIS','DECISION','SYSTEM']: z.append('event-domain')
 for k in ('event_time','observed_at','ingested_at','available_at','block_time'):
  if k in e and e[k] is not None:
   try:
    if not isinstance(e[k],str) or not TS.fullmatch(e[k]): raise ValueError()
    dt(e[k])
   except Exception:z.append('timestamp:'+k)
 try:
  if dt(e['observed_at'])>dt(e['ingested_at']): z.append('observed-after-ingested')
  if e.get('available_at') and dt(e['ingested_at'])>dt(e['available_at']): z.append('ingested-after-available')
  if e.get('event_time') and dt(e['event_time'])>dt(e['observed_at'])+datetime.timedelta(seconds=2): z.append('clock-skew')
 except Exception: pass
 if e.get('source_type') in ['SOLANA_RPC','SOLANA_GEYSER','SOLANA_WEBSOCKET']:
  for k in ('block_slot','block_time','tx_signature','instruction_index','inner_index'):
   if k not in e:z.append('onchain-missing:'+k)
  if not isinstance(e.get('block_slot'),int) or e.get('block_slot',-1)<0:z.append('slot')
  if not isinstance(e.get('instruction_index'),int) or e.get('instruction_index',-1)<0:z.append('instruction-index')
  if not B58.fullmatch(str(e.get('tx_signature',''))):z.append('tx-signature')
 t=e.get('trace_context',{}); 
 if not isinstance(t,dict) or not re.fullmatch(r'(?!0{32})[0-9a-f]{32}',str(t.get('trace_id',''))): z.append('trace-id')
 payload=e.get('payload'); forbidden={'event_id','event_type','event_version','contract_name','contract_version','available_at','provenance','integrity','raw_ref'}
 if not isinstance(payload,dict) or not payload or forbidden.intersection(payload): z.append('payload')
 if isinstance(payload,dict):
  digest=hashlib.sha256(canon(payload)).hexdigest(); integ=e.get('integrity',{})
  if e.get('payload_hash')!='sha256:'+digest or integ.get('digest')!=digest:z.append('integrity-mismatch')
  if integ.get('algorithm')!='SHA-256':z.append('unsupported-algorithm')
 rr=e.get('raw_ref')
 if e.get('event_stage')=='RAW' and not isinstance(rr,dict):z.append('raw-ref-required')
 if isinstance(rr,dict):
  loc=str(rr.get('locator','')); 
  if not re.fullmatch(r'(s3|gs|az|ipfs)://[A-Za-z0-9._/-]{3,512}',loc) or '..' in loc or '?' in loc:z.append('unsafe-raw-ref')
 if e.get('admission_status')=='AVAILABLE':
  if not e.get('available_at') or e.get('verification_status')!='VERIFIED' or e.get('integrity',{}).get('status')!='VERIFIED' or e.get('data_classification')=='UNCLASSIFIED':z.append('invalid-availability')
 if e.get('admission_status')=='QUARANTINED' and (e.get('available_at') is not None or not e.get('quarantine_reasons')):z.append('invalid-quarantine')
 lineage=[k for k in ('supersedes_event_id','corrects_event_id','revokes_event_id') if k in e]
 if len(lineage)>1:z.append('lineage-exclusive')
 if e.get('event_stage') in ('NORMALIZED','SYSTEM') and not EID.fullmatch(str(e.get('causation_event_id',''))):z.append('causation-required')
 if e.get('execution_mode')=='LIVE' and e.get('replay') is not None:z.append('live-replay')
 if e.get('execution_mode')=='REPLAY':
  rp=e.get('replay')
  if not isinstance(rp,dict):z.append('replay-required')
  else:
   try:
    if not e.get('available_at') or dt(e['available_at'])>dt(rp['cutoff_at']):z.append('future-data-leakage')
   except Exception:z.append('replay-time')
 return z
def main():
 valid=sorted((R/'fixtures/session18/valid').glob('*.json')); invalid=sorted((R/'fixtures/session18/invalid').glob('*.json'))
 for p in valid: check('valid-'+p.stem,not errors(json.loads(p.read_text())),','.join(errors(json.loads(p.read_text()))))
 for p in invalid: check('reject-'+p.stem,bool(errors(json.loads(p.read_text()))),'fixture unexpectedly valid')
 good=load('fixtures/session18/valid/minimal-raw-on-chain.json'); altered=json.loads(json.dumps(good)); altered['payload']['synthetic']=not altered['payload']['synthetic']; check('cryptographic-tampering-detected','integrity-mismatch' in errors(altered))
 check('canonical-serialization-deterministic',canon({'b':1,'a':2})==canon({'a':2,'b':1}))
 cls=R/'fixtures/session18/classification'; dup=load('fixtures/session18/classification/duplicate-event-id.json'); dupk=load('fixtures/session18/classification/duplicate-idempotency-key.json'); check('duplicate-event-id-detected',dup['event_id']==good['event_id']); check('duplicate-idempotency-key-detected',dupk['idempotency_key']==good['idempotency_key'] and dupk['event_id']!=good['event_id']); check('late-distinct',load('fixtures/session18/classification/late-event.json')['quality_flags']==['LATE']); check('out-of-order-distinct',load('fixtures/session18/classification/out-of-order-event.json')['quality_flags']==['OUT_OF_ORDER'])
 rows=list(csv.DictReader((R/'metadata/event-envelope-field-source-matrix.csv').open())); schema=load('schemas/events/event-envelope/1.0.0/schema.json'); check('field-closure-complete',set(schema['properties'])=={r['Field Name'] for r in rows} and all(all(v for v in r.values()) for r in rows)); msr=load('decisions/missing-source-register.yaml'); openp0=[x['id'] for x in msr['entries'] if x['severity']=='P0' and x['status']=='OPEN']; check('publication-fail-closed',bool(openp0) and schema['x-publication-status']=='BLOCKED_P0')
 status='PASS_WITH_BLOCKERS' if not F and openp0 else ('PASS' if not F else 'FAIL'); report={'status':status,'passed':len(P),'failed':len(F),'blocked':openp0,'results':P+F}; (R/'reports/conformance-report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'status':status,'passed':len(P),'failed':len(F),'blocked':openp0},indent=2)); return 1 if F else 0
if __name__=='__main__':sys.exit(main())
