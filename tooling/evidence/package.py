#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[2]
workspace = root.parent

def make_zip(target, files):
    with ZipFile(target, 'w', ZIP_DEFLATED) as z:
        for p, arc in files:
            z.write(p, arc)

repo_files=[]
for p in sorted(root.rglob('*')):
    if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts:
        repo_files.append((p, str(Path('dex-ai-contracts') / p.relative_to(root))))
make_zip(workspace/'dex-ai-contracts-session-17.zip', repo_files)

evidence_roots=['evidence/latest','reports','decisions','metadata']
evidence_files=[]
for rel in evidence_roots:
    for p in sorted((root/rel).rglob('*')):
        if p.is_file(): evidence_files.append((p,str(p.relative_to(root))))
make_zip(workspace/'dex-ai-contracts-bootstrap-evidence-pack.zip', evidence_files)
