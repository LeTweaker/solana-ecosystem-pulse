import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import solana_pulse as s
class TestCore(unittest.TestCase):
    def test_rpc_metrics(self):
        f=json.loads((ROOT/'tests/fixture.json').read_text())
        n=s.parse_rpc(f['rpc'])
        self.assertEqual(n['active_validators'],3)
        self.assertEqual(n['delinquent_validators'],1)
        self.assertGreater(n['avg_tps_12m'],100000)
        self.assertGreater(n['epoch_progress_pct'],40)
    def test_outputs(self):
        cfg=json.loads((ROOT/'config.json').read_text());d=s.merge_sources(json.loads((ROOT/'tests/fixture.json').read_text()),{},cfg,True)
        with tempfile.TemporaryDirectory() as td:
            s.write_outputs(d,td)
            for f in ['report.json','report.md','dashboard.html']:
                p=Path(td)/f;self.assertTrue(p.exists());self.assertGreater(p.stat().st_size,200)
            self.assertIn('TEST FIXTURE',(Path(td)/'report.md').read_text())
            self.assertIn('Solana Ecosystem Pulse',(Path(td)/'dashboard.html').read_text())
    def test_anomaly_threshold(self):
        cfg={'thresholds':{'delinquent_pct_high':1}}
        d={'network':{'delinquent_pct':7,'avg_tps_12m':2000,'avg_slot_ms_12m':400},'economics':{}}
        self.assertTrue(any(x['metric']=='delinquent_pct' for x in s.anomalies(d,cfg)))
if __name__=='__main__': unittest.main()