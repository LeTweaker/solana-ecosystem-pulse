#!/usr/bin/env python3
"""Solana Ecosystem Pulse: stdlib-only auto-updating report generator."""
from __future__ import annotations
import argparse,concurrent.futures,datetime as dt,html,json,os,statistics,time,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_RPC=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
def utcnow(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def get_json(url,timeout=15):
 req=urllib.request.Request(url,headers={"User-Agent":"solana-ecosystem-pulse/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())
def post_json(url,payload,timeout=20):
 req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"User-Agent":"solana-ecosystem-pulse/1.0","Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())
def rpc_batch(url):
 ms=[("slot","getSlot",[]),("block_height","getBlockHeight",[]),("epoch","getEpochInfo",[]),("performance","getRecentPerformanceSamples",[12]),("votes","getVoteAccounts",[]),("supply","getSupply",[{"commitment":"finalized"}]),("inflation","getInflationRate",[])]
 raw=post_json(url,[{"jsonrpc":"2.0","id":i+1,"method":m,"params":p} for i,(_,m,p) in enumerate(ms)])
 return {n:next((x.get("result") for x in raw if x.get("id")==i+1),None) for i,(n,_,_) in enumerate(ms)}
def parse_rpc(r):
 perf=r.get("performance") or [];t=[x.get("numTransactions",0)/max(1,x.get("samplePeriodSecs",1)) for x in perf];sl=[1000*x.get("samplePeriodSecs",0)/max(1,x.get("numSlots",1)) for x in perf if x.get("samplePeriodSecs") and x.get("numSlots")]
 v=r.get("votes") or {};cur=v.get("current") or [];bad=v.get("delinquent") or [];st=sorted([(int(x.get("activatedStake") or 0),x.get("nodePubkey") or x.get("votePubkey"),x.get("commission")) for x in cur],reverse=True);tot=sum(x[0] for x in st);ep=r.get("epoch") or {};sv=(r.get("supply") or {}).get("value") or {}
 return {"slot":r.get("slot"),"block_height":r.get("block_height"),"epoch":ep.get("epoch"),"epoch_progress_pct":100*ep.get("slotIndex",0)/ep["slotsInEpoch"] if ep.get("slotsInEpoch") else None,"avg_tps_12m":statistics.fmean(t) if t else None,"median_tps_12m":statistics.median(t) if t else None,"avg_slot_ms_12m":statistics.fmean(sl) if sl else None,"active_validators":len(cur),"delinquent_validators":len(bad),"delinquent_pct":100*len(bad)/(len(cur)+len(bad)) if cur or bad else None,"active_stake_sol":tot/1e9 if tot else None,"top10_stake_pct":100*sum(x[0] for x in st[:10])/tot if tot else None,"top_validators":[{"identity":x[1],"stake_sol":x[0]/1e9,"commission_pct":x[2]} for x in st[:10]],"circulating_supply_sol":sv.get("circulating",0)/1e9 if sv.get("circulating") is not None else None,"total_supply_sol":sv.get("total",0)/1e9 if sv.get("total") is not None else None,"inflation_rate_pct":(r.get("inflation") or {}).get("total")*100 if r.get("inflation") else None}
def fetch_defillama():
 tvl=get_json("https://api.llama.fi/v2/historicalChainTvl/Solana");dex=get_json("https://api.llama.fi/summary/dexs/Solana?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true");st=get_json("https://stablecoins.llama.fi/stablecoinchains");series=[{"date":x.get("date"),"tvl_usd":x.get("tvl")} for x in (tvl or [])[-31:]];sol=next((x for x in st if str(x.get("name","")).lower()=="solana"),{})
 return {"tvl_usd":series[-1]["tvl_usd"] if series else None,"tvl_30d":series,"dex_volume_24h_usd":dex.get("total24h"),"dex_volume_7d_usd":dex.get("total7d"),"dex_change_1d_pct":dex.get("change_1d"),"stablecoin_supply_usd":(sol.get("totalCirculatingUSD") or {}).get("peggedUSD") if isinstance(sol.get("totalCirculatingUSD"),dict) else sol.get("totalCirculatingUSD")}
def fetch_market():
 s=get_json("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&include_24hr_change=true&include_market_cap=true").get("solana",{});return {"sol_price_usd":s.get("usd"),"sol_24h_change_pct":s.get("usd_24h_change"),"sol_market_cap_usd":s.get("usd_market_cap")}
def fetch_development():
 r=get_json("https://api.github.com/repos/anza-xyz/agave/releases?per_page=5");c=get_json("https://api.github.com/repos/solana-foundation/solana-improvement-documents/commits?per_page=8")
 return {"agave_releases":[{"tag":x.get("tag_name"),"published_at":x.get("published_at"),"url":x.get("html_url")} for x in r[:5]],"recent_simd_commits":[{"sha":x.get("sha","")[:8],"date":((x.get("commit") or {}).get("author") or {}).get("date"),"message":((x.get("commit") or {}).get("message") or "").splitlines()[0],"url":x.get("html_url")} for x in c[:8]]}
def fetch_news():
 req=urllib.request.Request("https://solana.com/news/rss.xml",headers={"User-Agent":"solana-ecosystem-pulse/1.0"})
 with urllib.request.urlopen(req,timeout=15) as r:root=ET.fromstring(r.read())
 out=[]
 for x in root.findall(".//item")[:10]:
  title=(x.findtext("title") or "").strip()
  if title:out.append({"title":title,"url":(x.findtext("link") or "").strip(),"published_at":(x.findtext("pubDate") or "").strip(),"category":(x.findtext("category") or "").strip()})
 return {"official_news":out}
def load_fixture(p):return json.loads(Path(p).read_text())
def pct_change(a,b):return None if a in (None,0) or b is None else 100*(b-a)/a
def anomalies(d,cfg):
 t=cfg.get("thresholds",{});n=d.get("network",{});e=d.get("economics",{});o=[]
 def add(l,m,msg,v):o.append({"level":l,"metric":m,"message":msg,"value":v})
 if n.get("avg_tps_12m") is not None and n["avg_tps_12m"]<t.get("tps_low",1500):add("warn","avg_tps_12m","TPS is below configured floor",n["avg_tps_12m"])
 if n.get("avg_slot_ms_12m") is not None and n["avg_slot_ms_12m"]>t.get("slot_ms_high",600):add("warn","avg_slot_ms_12m","Slot time is slower than configured ceiling",n["avg_slot_ms_12m"])
 if n.get("delinquent_pct") is not None and n["delinquent_pct"]>t.get("delinquent_pct_high",5):add("critical","delinquent_pct","Validator delinquency is elevated",n["delinquent_pct"])
 if e.get("sol_24h_change_pct") is not None and abs(e["sol_24h_change_pct"])>=t.get("sol_move_abs_pct",8):add("info","sol_24h_change_pct","SOL price moved sharply over 24h",e["sol_24h_change_pct"])
 s=e.get("tvl_30d") or []
 if len(s)>=8:
  ch=pct_change(s[-8].get("tvl_usd"),s[-1].get("tvl_usd"))
  if ch is not None and abs(ch)>=t.get("tvl_7d_abs_pct",10):add("info","tvl_7d_change_pct","TVL moved sharply over 7d",ch)
 return o
def merge_sources(parts,errors,cfg,fixture=False):
 d={"meta":{"generated_at":utcnow(),"fixture":fixture,"schema_version":1,"source_status":{k:("ok" if parts.get(k) else "error") for k in ["rpc","defillama","market","development","news"]},"errors":errors},"network":parse_rpc(parts["rpc"]) if parts.get("rpc") else {},"economics":{**(parts.get("market") or {}),**(parts.get("defillama") or {})},"growth":{"tokenized_assets_note":"Tokenized equities volume is intentionally left source-pluggable; no reliable keyless canonical endpoint is assumed.","daily_active_addresses":None},"development":{**(parts.get("development") or {}),**(parts.get("news") or {})}}
 d["anomalies"]=anomalies(d,cfg);return d
def collect(cfg,fixture_path=None):
 if fixture_path:return merge_sources(load_fixture(fixture_path),{},cfg,True)
 tasks={"rpc":lambda:rpc_batch(cfg.get("rpc_url",DEFAULT_RPC)),"defillama":fetch_defillama,"market":fetch_market,"development":fetch_development,"news":fetch_news};parts={};errors={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
  fs={ex.submit(fn):n for n,fn in tasks.items()}
  for f,n in fs.items():
   try:parts[n]=f.result()
   except Exception as e:errors[n]=f"{type(e).__name__}: {e}"
 return merge_sources(parts,errors,cfg)
def fmt_num(v,d=1):
 if v is None:return "n/a"
 try:
  a=abs(v)
  if a>=1e12:return f"{v/1e12:.2f}T"
  if a>=1e9:return f"{v/1e9:.2f}B"
  if a>=1e6:return f"{v/1e6:.2f}M"
  if a>=1e3:return f"{v/1e3:.1f}K"
  return f"{v:.{d}f}" if isinstance(v,float) else str(v)
 except:return str(v)
def render_markdown(d):
 n=d["network"];e=d["economics"];L=["# Solana Ecosystem Pulse","Generated: **"+d["meta"]["generated_at"]+"**"+("  · **TEST FIXTURE**" if d["meta"]["fixture"] else ""),"","## Network performance",f"- TPS (12-sample average): **{fmt_num(n.get('avg_tps_12m'))}**",f"- Slot time: **{fmt_num(n.get('avg_slot_ms_12m'))} ms**",f"- Block height: **{fmt_num(n.get('block_height'),0)}**",f"- Epoch: **{n.get('epoch','n/a')}** ({fmt_num(n.get('epoch_progress_pct'))}%)","","## Validator health",f"- Active validators: **{fmt_num(n.get('active_validators'),0)}**",f"- Delinquent validators: **{fmt_num(n.get('delinquent_validators'),0)}** ({fmt_num(n.get('delinquent_pct'))}%)",f"- Top-10 stake share: **{fmt_num(n.get('top10_stake_pct'))}%**","","## Economics",f"- SOL: **\${fmt_num(e.get('sol_price_usd'),2)}** ({fmt_num(e.get('sol_24h_change_pct'))}% 24h)",f"- TVL: **\${fmt_num(e.get('tvl_usd'))}**",f"- DEX volume 24h: **\${fmt_num(e.get('dex_volume_24h_usd'))}**",f"- Stablecoin supply: **\${fmt_num(e.get('stablecoin_supply_usd'))}**","","## Development signals"]
 for x in d.get("development",{}).get("agave_releases",[])[:3]:L.append(f"- Agave release {x.get('tag')} — {x.get('published_at')}")
 for x in d.get("development",{}).get("recent_simd_commits",[])[:4]:L.append(f"- SIMD activity {x.get('sha')} — {x.get('message')}")
 for x in d.get("development",{}).get("official_news",[])[:5]:L.append(f"- Official news — {x.get('title')}")
 L+=["","## Anomalies"]+([f"- **{x['level'].upper()}** · {x['message']} ({x['metric']} = {fmt_num(x['value'])})" for x in d["anomalies"]] or ["- No configured thresholds triggered."])
 if d["meta"]["errors"]:L+=["","## Source health"]+[f"- {k}: {v}" for k,v in d["meta"]["errors"].items()]
 return "\\n".join(L)+"\\n"
def render_html(d):
 e=d["economics"];n=d["network"];cards=[("TPS",n.get("avg_tps_12m"),""),("Slot time",n.get("avg_slot_ms_12m")," ms"),("Active validators",n.get("active_validators"),""),("Delinquent",n.get("delinquent_pct"),"%"),("SOL",e.get("sol_price_usd")," USD"),("TVL",e.get("tvl_usd")," USD"),("DEX 24h",e.get("dex_volume_24h_usd")," USD"),("Stablecoins",e.get("stablecoin_supply_usd")," USD")]
 payload=json.dumps(d,separators=(",",":")).replace("</","<\\\\/")
 cardhtml="".join("<article class='card'><span>"+html.escape(k)+"</span><strong>"+html.escape(fmt_num(v))+html.escape(s)+"</strong></article>" for k,v,s in cards)
 alerts="".join("<li class='"+x["level"]+"'><b>"+x["level"].upper()+"</b> "+html.escape(x["message"])+"</li>" for x in d["anomalies"]) or "<li>No configured thresholds triggered.</li>"
 return "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Solana Ecosystem Pulse</title><style>body{margin:0;background:#070a12;color:#ecf2ff;font:14px system-ui;padding:28px}main{max-width:1180px;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.card,.panel{background:#101625;border:1px solid #202a40;border-radius:16px;padding:18px}.card span{display:block;color:#8ea1c0;font-size:12px;text-transform:uppercase}.card strong{display:block;font-size:24px;margin-top:6px}.cols{display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-top:14px}@media(max-width:800px){.cols{grid-template-columns:1fr}}.critical{color:#fb7185}.warn{color:#fbbf24}.info{color:#38bdf8}code{color:#14f195}a{color:#ecf2ff}</style></head><body><main><header><small>SOLANA ECOSYSTEM INTELLIGENCE</small><h1>Pulse</h1><p>Network · validators · economics · development</p></header><section class='grid'>"+cardhtml+"</section><section class='cols'><div class='panel'><h2>TVL · 30 days</h2><canvas id='chart' width='800' height='250'></canvas></div><div class='panel'><h2>Anomaly radar</h2><ul>"+alerts+"</ul><h3>Source health</h3><div id='sources'></div></div></section><section class='panel'><h2>Top validators by active stake</h2><div id='validators'></div></section><section class='panel'><h2>Official ecosystem news</h2><div id='news'></div></section></main><script>const D="+payload+";const c=document.getElementById('chart'),x=c.getContext('2d'),s=(D.economics.tvl_30d||[]).map(z=>z.tvl_usd).filter(Number.isFinite);if(s.length>1){let mn=Math.min(...s),mx=Math.max(...s);x.strokeStyle='#8b5cf6';x.lineWidth=3;x.beginPath();s.forEach((v,i)=>{let px=16+i*(c.width-32)/(s.length-1),py=c.height-16-(v-mn)*(c.height-32)/Math.max(1,mx-mn);i?x.lineTo(px,py):x.moveTo(px,py)});x.stroke()}document.getElementById('sources').innerHTML=Object.entries(D.meta.source_status).map(function(a){return '<div><code>'+a[0]+'</code> · '+a[1]+'</div>'}).join('');document.getElementById('validators').innerHTML=(D.network.top_validators||[]).map(function(v,i){return '<div>#'+(i+1)+' <code>'+v.identity+'</code> · '+(v.stake_sol||0)+' SOL · '+(v.commission_pct==null?'n/a':v.commission_pct)+'%</div>'}).join('');document.getElementById('news').innerHTML=(D.development.official_news||[]).map(function(n){return '<p><a href='+JSON.stringify(n.url)+' target=_blank>'+n.title+'</a><br><small>'+n.published_at+'</small></p>'}).join('')||'<p>No news available.</p>';</script></body></html>"
def write_outputs(d,outdir):
 o=Path(outdir);o.mkdir(parents=True,exist_ok=True);(o/"report.json").write_text(json.dumps(d,indent=2)+"\\n");(o/"report.md").write_text(render_markdown(d));(o/"dashboard.html").write_text(render_html(d))
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--config",default=str(ROOT/"config.json"));p.add_argument("--out",default=str(ROOT/"output"));p.add_argument("--fixture");p.add_argument("--once",action="store_true");p.add_argument("--watch",action="store_true");a=p.parse_args(argv);cfg=json.loads(Path(a.config).read_text())
 while True:
  d=collect(cfg,a.fixture);write_outputs(d,a.out);print(json.dumps({"generated_at":d["meta"]["generated_at"],"errors":d["meta"]["errors"],"anomalies":len(d["anomalies"])}))
  if not a.watch:break
  time.sleep(max(60,int(cfg.get("refresh_seconds",900))))
if __name__=="__main__":main()
