#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],check=True,cwd=ROOT)
with tempfile.TemporaryDirectory() as td:
    subprocess.run([sys.executable,str(ROOT/'src/solana_pulse.py'),'--fixture',str(ROOT/'tests/fixture.json'),'--out',td],check=True,cwd=ROOT)
    out=Path(td)
    data=json.loads((out/'report.json').read_text())
    assert data['meta']['fixture'] is True
    assert data['network']['active_validators'] is not None
    assert data['development']['official_news']
    assert 'TEST FIXTURE' in (out/'report.md').read_text()
    assert 'Anomaly radar' in (out/'dashboard.html').read_text()
print('QA PASS: tests, render, fixture marking, core fields, news, dashboard')