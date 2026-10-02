import sys, tempfile, json, sqlite3, importlib.util
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path.cwd()/'src'))
from rebalance.ingest.clio import ensure_clio_schema,clio_semantic_docs,sync_clio_prompts
import rebalance.ingest.clio as clio
spec=importlib.util.spec_from_file_location('dws',Path.cwd()/'utils/daily_work_synthesis.py'); dws=importlib.util.module_from_spec(spec);spec.loader.exec_module(dws)
failures=[]
original_reader=dws.recent_prompt_rows
with tempfile.TemporaryDirectory() as t:
 root=Path(t);log=root/'events.jsonl'; source={'record_id':'clio1-synthetic-a','origin_id':'synthetic-origin-a','timestamp':'2026-10-02T22:00:00Z','session_id':'synthetic-session','prompt':'Synthetic Unicode separator \u2028 remains in one JSONL record','agent':'codex','repo':'HiQS-Labs/XYZ-forge'}
 log.write_text(json.dumps(source,ensure_ascii=False)+'\n');dws.resolve_clio_prompt_log_path=lambda:log
 recent=dws.recent_prompt_rows(datetime.fromisoformat('2026-10-02T21:00:00+00:00'))
 try:assert len(recent)==1 and recent[0]['prompt']==source['prompt']
 except AssertionError:failures.append('LF-only JSONL boundary')
 # Stub scanners only: synthetic packet never touches live prompts or network.
 dws._scanner_json=lambda *a:{}
 dws.shared_issue_status_packet=lambda *a,**k:{}
 dws.recent_prompt_rows=lambda *a:[source]
 packet=dws.collect_packet(root/'missing.db',datetime.fromisoformat('2026-10-02T22:01:00+00:00'),root,cfg={})
 try:assert any(x['id']=='clio:clio1-synthetic-a' for x in packet['evidence'])
 except AssertionError:failures.append('stable canonical Daily evidence ID')
 clio.resolve_clio_prompt_log_path=lambda:log
 db=root/'consumer.db'; first=sync_clio_prompts(db);second=sync_clio_prompts(db)
 con=sqlite3.connect(db);con.row_factory=sqlite3.Row;docs=list(clio_semantic_docs(con))
 try:
  assert len(docs)==1 and second.prompts_inserted==0
  assert docs[0].metadata['source_records']==[{'record_id':source['record_id'],'origin_id':source['origin_id']}]
 except (AssertionError,KeyError):failures.append('canonical provenance retained idempotently')
 source['record_id']='clio1-synthetic-b';source['origin_id']='synthetic-origin-b';log.write_text(json.dumps(source)+'\n');sync_clio_prompts(db)
 try:
  docs=list(clio_semantic_docs(con));assert len(docs)==1 and len(docs[0].metadata['source_records'])==2
 except (AssertionError,KeyError):failures.append('multiple origin references preserved without duplicate consumer IDs')
from rebalance.ingest.semantic_index import project_semantic_documents
from rebalance.ingest.clio import load_recent_clio_prompts
with tempfile.TemporaryDirectory() as t:
 root=Path(t);log=root/'events.jsonl';db=root/'consumer.db'
 rows=[{'record_id':'clio1-a','origin_id':'origin-a','timestamp':'2026-10-02T22:00:00Z','session_id':'session','prompt':'Unicode \u0085 \u2028 \u2029 intact','agent':'codex','repo':'x'}, {'record_id':'clio1-b','origin_id':'origin-b','timestamp':'2026-10-02T22:00:00Z','session_id':'session','prompt':'Unicode \u0085 \u2028 \u2029 intact','agent':'codex','repo':'x'}]
 clio.resolve_clio_prompt_log_path=lambda:log;log.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
 try:
  sync_clio_prompts(db); before=sqlite3.connect(db).execute('SELECT COUNT(*) FROM clio_prompts').fetchone()[0]
  log.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in reversed(rows)));result=sync_clio_prompts(db)
  cached=load_recent_clio_prompts(db,'2026-10-02T21:00:00Z')
  assert before==1 and result.prompts_inserted==0 and len(cached[0]['source_records'])==2
 except (AssertionError,KeyError,sqlite3.IntegrityError):failures.append('same-pass collision / reordered replay / cached provenance')
 try:
  result=project_semantic_documents(db,source_types=['clio']);assert result.total_documents==1
  conn=sqlite3.connect(db);meta=json.loads(conn.execute("SELECT metadata_json FROM semantic_documents WHERE source_type='clio'").fetchone()[0]);assert len(meta['source_records'])==2
 except (AssertionError,KeyError,TypeError,sqlite3.Error):failures.append('maintenance facade materializes nonempty CLIO metadata without embedding')
 dws.resolve_clio_prompt_log_path=lambda:log
 dws.recent_prompt_rows=original_reader
 try:assert len(dws.recent_prompt_rows(datetime.fromisoformat('2026-10-02T21:00:00+00:00')))==2
 except AssertionError:failures.append('all three Unicode separators remain in LF-delimited records')
print(json.dumps({'checks':7,'failures':failures,'passed':7-len(failures)}));sys.exit(bool(failures))
