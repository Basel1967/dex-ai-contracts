#!/usr/bin/env python3
import copy, datetime, hashlib, json, pathlib, re, sys

R = pathlib.Path(__file__).resolve().parents[2]
P, F = [], []
TS = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$')
EVENT = re.compile(r'^urn:dex-ai:event:[0-9a-f]{32}$')
RAW = re.compile(r'^urn:dex-ai:raw:[0-9a-f]{64}$')
SEMVER = re.compile(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$')
REQUIRED = {'normalization_status','source_raw_event_id','source_raw_payload_ref','normalizer_name','normalizer_version','normalization_profile','normalized_event_type','normalized_entity_refs','normalized_data','field_lineage','normalization_warnings','normalization_errors','source_schema_ref','normalization_started_at','normalization_completed_at'}

def load(path): return json.loads((R / path).read_text())
def dt(value): return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
def check(name, condition, detail=''): (P if condition else F).append({'test': name, 'passed': bool(condition), 'detail': '' if condition else detail})

def errors(p):
    z=[]
    if not isinstance(p, dict): return ['payload-not-object']
    z += ['missing:'+x for x in sorted(REQUIRED-set(p))]
    z += ['unknown:'+x for x in sorted(set(p)-REQUIRED)]
    status=p.get('normalization_status')
    if status not in {'SUCCESS','PARTIAL','FAILED'}: z.append('normalization-status')
    if not EVENT.fullmatch(str(p.get('source_raw_event_id',''))): z.append('source-raw-event-id')
    if not RAW.fullmatch(str(p.get('source_raw_payload_ref',''))): z.append('source-raw-payload-ref')
    if not SEMVER.fullmatch(str(p.get('normalizer_version',''))): z.append('normalizer-version')
    if p.get('normalized_event_type') != 'MINT_INITIALIZED': z.append('event-type-not-authorized')
    data=p.get('normalized_data'); lineage=p.get('field_lineage'); warnings=p.get('normalization_warnings'); errs=p.get('normalization_errors')
    if status == 'SUCCESS' and errs: z.append('success-with-errors')
    if status == 'SUCCESS' and not lineage: z.append('missing-field-lineage')
    if status == 'PARTIAL' and not (warnings or errs): z.append('partial-without-diagnostic')
    if status == 'FAILED' and data is not None: z.append('failed-with-data')
    if status == 'FAILED' and not errs: z.append('failed-without-error')
    if status in {'SUCCESS','PARTIAL'}:
        if not isinstance(data,dict) or set(data)!={'mint_address','synthetic'}: z.append('normalized-data-shape')
        else:
            if not isinstance(data['synthetic'],bool): z.append('synthetic-type')
            if not isinstance(data['mint_address'],str) or not 32<=len(data['mint_address'])<=44: z.append('mint-address')
        paths={x.get('normalized_path') for x in lineage} if isinstance(lineage,list) and all(isinstance(x,dict) for x in lineage) else set()
        if data is not None and paths != {'/normalized_data/mint_address','/normalized_data/synthetic'}: z.append('lineage-coverage')
    try:
        if not TS.fullmatch(p['normalization_started_at']) or not TS.fullmatch(p['normalization_completed_at']) or dt(p['normalization_completed_at']) < dt(p['normalization_started_at']): z.append('normalization-time-order')
    except Exception: z.append('normalization-time-order')
    return sorted(set(z))

def main():
    schema=load('schemas/events/normalized-event/1.0.0/schema.json')
    check('schema-draft-2020-12',schema.get('$schema')=='https://json-schema.org/draft/2020-12/schema')
    check('schema-closed',schema.get('additionalProperties') is False)
    check('candidate-not-published',schema.get('x-publication-status')=='NOT_PUBLISHED')
    good=load('fixtures/session24/normalized-event/valid/success-mint-initialized.json')
    failed=load('fixtures/session24/normalized-event/valid/failed.json')
    check('success-valid',not errors(good),','.join(errors(good)))
    check('failed-attempt-preserved',not errors(failed),','.join(errors(failed)))
    for path in sorted((R/'fixtures/session24/normalized-event/invalid').glob('*.json')):
        case=json.loads(path.read_text()); base=load('fixtures/session24/normalized-event/'+case['base']); value=copy.deepcopy(base); value.update(case['mutation']); found=errors(value)
        check('reject-'+path.stem,case['expected_error'] in found,','.join(found))
    reg=load('registry/schemas/index.yaml'); graph=load('registry/dependencies/graph.yaml')
    published={x['id']:x for x in reg['artifacts'] if x.get('publication')=='PUBLISHED'}
    check('published-dependencies-retained',set(published)=={'urn:dex-ai:schema:event:event-envelope','urn:dex-ai:schema:event:raw-event'})
    check('normalized-candidate-registered',any(x['id']=='urn:dex-ai:schema:event:normalized-event' and x['publication']=='NOT_PUBLISHED' for x in reg['artifacts']))
    check('no-later-contract',graph.get('next_contract')=='urn:dex-ai:schema:event:normalized-event:1.0.0' and graph.get('later_contracts_started') is False)
    for name,expected in [('event-envelope-v1.0.0.tar.gz','3bb89e3665261703dc22e94808d6c5e9bed114c29c66fdbd37904e01d98f4120'),('raw-event-v1.0.0.tar.gz','b0d5b5215d7c5a4dfd4e950655f671cac2628ef627d2a2062b9081cdfa40cd48')]:
        check('immutable-'+name,hashlib.sha256((R/'releases/out'/name).read_bytes()).hexdigest()==expected)
    report={'session':'SESSION 24','contract':'Normalized Event 1.0.0','status':'PASS' if not F else 'FAIL','passed':len(P),'failed':len(F),'results':P+F}
    (R/'reports/session24-normalized-event-conformance-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'passed':len(P),'failed':len(F)},indent=2)); return 0 if not F else 1

if __name__ == '__main__': sys.exit(main())
