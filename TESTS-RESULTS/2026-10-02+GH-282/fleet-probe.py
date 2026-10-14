import fcntl, hashlib, importlib.util, os, shutil, subprocess, tempfile
from pathlib import Path
from unittest.mock import patch
from rebalance.ingest import config,pulse,sync_snapshot
from rebalance.lib.git_ops import fleet_output_path,fleet_settings,run_git
from rebalance.ingest.pulse_health import read_collector_health
ROOT=Path(os.environ["QA_REPO_ROOT"]).resolve()
CLIO=Path(os.environ['QA_CLIO_HELPER'])
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True,stderr=subprocess.STDOUT).strip()
def check(ok,label):
 assert ok,label
 print('PASS',label,flush=True)
with tempfile.TemporaryDirectory(prefix='gh282-fleet-') as tmp:
 base=Path(tmp);remote=base/'remote.git';subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
 seed=base/'seed';subprocess.run(['git','clone',str(remote),str(seed)],check=True,capture_output=True)
 for k,v in [('user.name','Fixture'),('user.email','fixture@example.invalid')]:git(seed,'config',k,v)
 (seed/'README.md').write_text('synthetic fleet\n');git(seed,'add','README.md');git(seed,'commit','-m','seed');git(seed,'push','-u','origin','HEAD')
 spec=importlib.util.spec_from_file_location('clio',CLIO);clio=importlib.util.module_from_spec(spec);spec.loader.exec_module(clio); clio.CONFIG=base/"unused-config.json"
 devices=[]
 for n in range(4):
  device=f'mac-{n}';repo=base/device;private=base/f'config-{n}';private.mkdir()
  subprocess.run(['git','clone',str(remote),str(repo)],check=True,capture_output=True)
  for k,v in [('user.name','Fixture'),('user.email','fixture@example.invalid')]:git(repo,'config',k,v)
  db=private/'clio.sqlite3';owner=clio.initialize(db)
  clio.capture(db,owner,{'timestamp':'2026-10-02T17:00:00Z','prompt':f'synthetic fixture {n}','repo':'fixture','machine':device,'agent':'qa','session_id':device})
  (private/'config.sh').write_text(f'device_id="{device}"\nhostname="{device}"\nsync_repo_dir="{repo}"\nfleet_mode=true\nfleet_sync_subdir="sync"\nfleet_stagger_max_seconds=0\nclio_owner_uuid="{owner}"\nclio_store_path="{CLIO}"\nclio_database="{db}"\nrepos=()\n')
  if n == 0:
   foreign_db=private/'foreign.sqlite3';foreign=clio.initialize(foreign_db)
   clio.capture(foreign_db,foreign,{'timestamp':'2026-10-02T17:00:00Z','prompt':'foreign synthetic fixture','repo':'fixture','machine':'foreign','agent':'qa','session_id':'foreign'})
   foreign_snapshot=private/'foreign.jsonl';clio.export_device(foreign_db,foreign_snapshot);clio.import_device(db,foreign_snapshot)
   with clio.database(db) as conn:check(conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]==2,'foreign history retained locally')
  cfg={'pulse_fleet_enabled':True,'pulse_device_id':device,'pulse_target_path':str(repo),'sync_subdir':'sync'}
  with patch.dict(os.environ,{'GIT_PULSE_CONFIG_DIR':str(private),'CLIO_CONFIG':str(private/'clio-storage.json')}),patch.object(config,'get_pulse_config',return_value=cfg),patch.object(pulse,'get_pulse_config',return_value=cfg):
   rel=fleet_output_path(cfg,'live-pulse.md');body=f'# {device}\nfixture\n'
   result=pulse._commit_and_push_if_changed(repo,rel,body,push=True,commit_message='pulse: fixture')
   check(result.get('queued') and not result.get('pushed'),'commit-only '+device)
   with patch.object(pulse,'_publish_pulse',return_value={'ok':True,'git':result,'markdown_sha256':hashlib.sha256(body.encode()).hexdigest()}):
    status=pulse.publish_pulse(Path('unused'))
   check(not status.get('status_error'),'owned status '+device)
   check(run_git(repo,'show',f'@{{u}}:{rel}').returncode!=0,'not delivered before collector '+device)
   for source in ('calendar','email'):
    sync_snapshot._write_snapshot(repo/'sync',source,device,{'schema_version':1,'source':source,'device_id':device,'generated_at':'2026-10-02T17:00:00Z','row_count':0,'rows':[]})
   sync_snapshot._update_latest_pointer(repo/'sync/calendar',device,'2026-10-02T17:00:00Z')
   check(not (repo/'sync/calendar/latest.json').exists(),'no shared pointer '+device)
   check(sync_snapshot.commit_and_push_sync(repo,'sync',device_id=device,generated_at='fixture').get('queued'),'sync queued '+device)
   try:fleet_settings({**cfg,'pulse_device_id':'wrong'})
   except ValueError:pass
   else:raise AssertionError('mismatch accepted')
  devices.append((device,repo,private,owner))
 processes=[]
 for device,repo,private,owner in devices:
  env={**os.environ,'GIT_PULSE_CONFIG_DIR':str(private),'CLIO_CONFIG':str(private/'clio-storage.json')}
  processes.append((device,subprocess.Popen(['/bin/bash',str(ROOT/'experimental/git-pulse/collect.sh')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)))
 for device,process in processes:
  out,err=process.communicate(timeout=180)
  if process.returncode:print(out,err,flush=True)
  check(process.returncode==0,'concurrent delivery '+device)
 repo=devices[0][1];git(repo,'pull','--rebase')
 for device,_,_,owner in devices:
  check((repo/f'devices/{device}/live-pulse.md').exists(),'page retained '+device)
  _,rows=clio.snapshot_records((repo/f'devices/{owner}/clio.jsonl').read_bytes(),owner)
  check(len(rows)==1 and rows[0]['origin_id']==owner,'canonical owner-only CLIO '+device)
 check(len(read_collector_health(repo))==4 and all(h.state=='ALIVE' for h in read_collector_health(repo)),'delivered fleet healthy')
 check(all(d in pulse.fleet_view(repo) for d,_,_,_ in devices),'derived fleet view')
 device,repo,private,_=devices[0];cfg={'pulse_fleet_enabled':True,'pulse_device_id':device,'pulse_target_path':str(repo),'sync_subdir':'sync'}
 with patch.dict(os.environ,{'GIT_PULSE_CONFIG_DIR':str(private)}),patch.object(config,'get_pulse_config',return_value=cfg),patch.object(pulse,'get_pulse_config',return_value=cfg),patch.object(pulse,'_publish_pulse',side_effect=RuntimeError('forced failure')):
  failure=pulse.publish_pulse(Path('unused')); check(failure.get('render_error'),'render failure red control')
 check(any(h.device_id==device and h.state=='ALIVE_NOT_PUBLISHING' for h in read_collector_health(repo)),'pending failure not healthy')
 env={**os.environ,'GIT_PULSE_CONFIG_DIR':str(private),'CLIO_CONFIG':str(private/'clio-storage.json')}
 result=subprocess.run(['/bin/bash',str(ROOT/'experimental/git-pulse/collect.sh')],env=env,capture_output=True,text=True,timeout=180)
 check(result.returncode==0,'failure status delivered')
 check(any(h.device_id==device and h.state=='ALIVE_NOT_PUBLISHING' for h in read_collector_health(repo)),'delivered failure visible')
 original=(repo/'README.md').read_bytes()
 (repo/'README.md').write_text('foreign authored dirt\n')
 result=subprocess.run(['/bin/bash',str(ROOT/'experimental/git-pulse/collect.sh')],env=env,capture_output=True,text=True,timeout=60)
 check(result.returncode!=0 and (repo/'README.md').read_text()=='foreign authored dirt\n','foreign dirt refused and preserved')
 (repo/'README.md').write_bytes(original)
 with (repo/'.git/rebalance-publish.lock').open('a+') as lock:
  fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  result=subprocess.run(['/bin/bash',str(ROOT/'experimental/git-pulse/collect.sh')],env=env,capture_output=True,text=True,timeout=60)
  check(result.returncode==75,'busy common lock skips with 75')
 pending_head=git(repo,'rev-parse','HEAD');watermark=(private/'last-run').read_bytes()
 owned_paths=[p.relative_to(repo).as_posix() for p in (repo/'devices'/device).rglob('*') if p.is_file()] + [f'devices/{devices[0][3]}/clio.jsonl',f'devices/{device}.yaml',f'pulse-{device}.md',f'sync/calendar/{device}.json',f'sync/email/{device}.json']
 owned_blobs={p:git(repo,'rev-parse',f'HEAD:{p}') for p in owned_paths}
 index=repo/'.git/index.lock';index.write_text('fixture-owned stale lock')
 result=subprocess.run(['/bin/bash',str(ROOT/'experimental/git-pulse/collect.sh')],env=env,capture_output=True,text=True,timeout=60)
 check(result.returncode!=0 and index.exists() and git(repo,'rev-parse','HEAD')==pending_head,'stale index lock refuses without lost commits')
 index.unlink()
 # A failed git-add can leave newer generated files dirty. The next collector
 # must commit those exact pending bytes before attempting delivery.
 owned_blobs={p:git(repo,'hash-object',p) for p in owned_paths}
 bindir=private/'bin';bindir.mkdir();wrapper=bindir/'git';real_git=shutil.which('git')
 wrapper.write_text('#!/usr/bin/env python3\nimport os,sys,time\nif "push" in sys.argv[1:]: time.sleep(5)\nos.execv('+repr(real_git)+', ["git",*sys.argv[1:]])\n');wrapper.chmod(0o700)
 slow_env={**env,'PATH':str(bindir)+os.pathsep+env['PATH'],'REBALANCE_GIT_TIMEOUT':'0.1'}
 result=subprocess.run(['/bin/bash',str(ROOT/'experimental/git-pulse/collect.sh')],env=slow_env,capture_output=True,text=True,timeout=90)
 check(result.returncode==2 and 'timeout' in result.stderr and all(git(repo,'rev-parse',f'HEAD:{p}')==blob for p,blob in owned_blobs.items()) and (private/'last-run').read_bytes()==watermark,'timed-out push exits 2 and preserves owned blobs/watermark')
 print('Synthetic probe only; live fleet qualification remains pending.',flush=True)
