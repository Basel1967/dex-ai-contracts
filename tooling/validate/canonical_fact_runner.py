#!/usr/bin/env python3
import copy, datetime, hashlib, json, pathlib, re, sys

R=pathlib.Path(__file__).resolve().parents[2]; P=[]; F=[]
TS=re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$')
REQ={'fact_id','fact_version','entity_id','entity_type','fact_type','fact_value','fact_status','valid_from','valid_to','recorded_at','supersedes_version','correction_reason','evidence','resolution_status','confidence','freshness','lineage','canonicalization_profile','schema_ref','idempotency_key','trace_id'}

def load(rel): return json.loads((R/rel).read_text())
def resolve(rel):
    v=load(rel)
    if 'base' not in v: return v
    base=resolve('fixtures/session26/canonical-fact/'+v['base']); base.update(copy.deepcopy(v['mutation'])); return base
def check(name,ok,detail=''): (P if ok else F).append({'test':name,'passed':bool(ok),'detail':'' if ok else detail})
def errors(x):
    z=[]
    if not isinstance(x,dict): return ['payload']
    z += ['missing:'+k for k in sorted(REQ-set(x))]; z += ['unknown:'+k for k in sorted(set(x)-REQ)]
    if x.get('entity_type')!='SOLANA_MINT' or x.get('fact_type')!='MINT_INITIALIZED': z.append('scope')
    v=x.get('fact_value',{})
    if v.get('initialized') is not True: z.append('initialized-false')
    if str(x.get('entity_id','')).split(':')[-1] != v.get('mint_address'): z.append('entity-value-mismatch')
    n=x.get('fact_version'); s=x.get('supersedes_version')
    if n==1 and s is not None or isinstance(n,int) and n>1 and s!=n-1: z.append('version-chain')
    ev=x.get('evidence',[])
    if not isinstance(ev,list) or not ev: z.append('evidence')
    else:
        seen={}
        for e in ev:
            eid=e.get('normalized_event_id'); h=e.get('normalized_payload_hash')
            if eid in seen and seen[eid]!=h: z.append('evidence-identity-integrity')
            seen[eid]=h
            if e.get('lineage_verified') is not True: z.append('unverified-evidence-lineage')
        contradiction=any(e.get('evidence_role')=='CONTRADICTS' for e in ev)
        if contradiction and x.get('fact_status')=='ACTIVE': z.append('active-contradiction')
        if contradiction and x.get('resolution_status')=='UNRESOLVED' and x.get('fact_status')!='CONFLICTED': z.append('conflict-state')
    if not isinstance(x.get('lineage'),dict) or x.get('lineage',{}).get('lineage_verified') is not True: z.append('lineage')
    c=x.get('confidence',{})
    if c.get('evidence_count') != len(ev): z.append('confidence-evidence-count')
    if c.get('status')=='NOT_ASSESSED' and any(c.get(k) is not None for k in ('score','method','assessed_at')): z.append('confidence-not-assessed')
    if c.get('status')=='ASSESSED' and (c.get('score') is None or not c.get('method') or not c.get('assessed_at')): z.append('confidence-method')
    if x.get('fact_status') in {'CORRECTED','RETRACTED'} and not x.get('correction_reason'): z.append('correction-reason')
    for k in ('valid_from','recorded_at'):
        if not TS.fullmatch(str(x.get(k,''))): z.append('timestamp')
    try:
        if x.get('valid_to') and x['valid_to'] < x['valid_from']: z.append('validity-order')
    except Exception: z.append('validity-order')
    return sorted(set(z))

def main():
    schema=load('schemas/facts/canonical-fact/1.0.0/schema.json')
    check('schema-draft-2020-12',schema.get('$schema')=='https://json-schema.org/draft/2020-12/schema')
    check('schema-closed-and-required',schema.get('additionalProperties') is False and set(schema.get('required',[]))==REQ)
    check('candidate-not-published',schema.get('x-publication-status')=='NOT_PUBLISHED')
    for name in ('active-mint-initialized','corrected-version','unresolved-conflict','late-confirmation'):
        found=errors(resolve('fixtures/session26/canonical-fact/valid/'+name+'.json')); check('accept-'+name,not found,','.join(found))
    for path in sorted((R/'fixtures/session26/canonical-fact/invalid').glob('*.json')):
        case=load(path.relative_to(R)); found=errors(resolve(path.relative_to(R))); check('reject-'+path.stem,case['expected_error'] in found,','.join(found))
    meta=load('metadata/canonical-fact-artifact-metadata.json'); trace=load('metadata/session26-canonical-fact-traceability.json')
    check('candidate-metadata',meta.get('artifact_id')=='urn:dex-ai:schema:fact:canonical-fact' and meta.get('publication_status')=='NOT_PUBLISHED')
    check('dependency-traceability',trace.get('dependency_chain',[None])[0]=='urn:dex-ai:schema:fact:canonical-fact:1.0.0' and trace.get('agents_started') is False and trace.get('services_started') is False)
    expected={'event-envelope-v1.0.0.tar.gz':'3bb89e3665261703dc22e94808d6c5e9bed114c29c66fdbd37904e01d98f4120','raw-event-v1.0.0.tar.gz':'b0d5b5215d7c5a4dfd4e950655f671cac2628ef627d2a2062b9081cdfa40cd48','normalized-event-v1.0.0-foundation-candidate.tar.gz':'348e1192e335eeaa037331dd7fd60758b2e89fef6ff84878c259902d606f4eda'}
    check('published-dependency-digests',all(hashlib.sha256((R/'releases/out'/k).read_bytes()).hexdigest()==v for k,v in expected.items()))
    report={'session':'SESSION 26','contract':'Canonical Fact 1.0.0','status':'PASS' if not F else 'FAIL','passed':len(P),'failed':len(F),'results':P+F}
    (R/'reports/session26-canonical-fact-conformance-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'passed':len(P),'failed':len(F)},indent=2)); return 0 if not F else 1
if __name__=='__main__': sys.exit(main())
