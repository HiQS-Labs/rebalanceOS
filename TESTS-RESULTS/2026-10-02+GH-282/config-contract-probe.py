from pathlib import Path
from unittest.mock import patch
import os,tempfile
from rebalance.lib.git_ops import publish_git_paths
from rebalance.ingest.pulse import publish_pulse
from rebalance.ingest.index_ops import _refresh_sync
from rebalance.doctor import _check_scheduler_liveness,_check_pulse_collectors
failed=[]
def check(name,fn):
 try:fn();print('PASS '+name)
 except Exception as e:failed.append(name);print('FAIL '+name+': '+type(e).__name__)
with tempfile.TemporaryDirectory(prefix='gh282-config-') as d:
 p=Path(d);collector=p/'config.sh';collector.write_text('device_id=fixture\nfleet_mode=true\nsync_repo_dir='+str(p)+'\n');(p/'com.rebalance-os.pulse-sync.plist').write_bytes(b'fixture')
 missing={'pulse_fleet_enabled':True,'pulse_device_id':'fixture','pulse_target_path':None,'sync_subdir':'sync'}
 mismatch=dict(missing,pulse_device_id='other',pulse_target_path=str(p))
 with patch.dict(os.environ,{'GIT_PULSE_CONFIG_DIR':d}):
  def target():
   with patch('rebalance.ingest.pulse.get_pulse_config',return_value=missing):
    r=publish_pulse(p/'unused.db');assert not r['ok'] and 'pulse_target_path' in r['error']
  check('real missing target returns config result',target)
  def publication():
   with patch('rebalance.ingest.config.get_pulse_config',return_value=mismatch),patch('rebalance.lib.git_ops.run_git') as run:
    r=publish_git_paths(p,['owned.md'],'fixture');assert r['git_error'] and not r['committed'] and not r['pushed'];run.assert_not_called()
  check('real collector identity mismatch refuses before Git',publication)
  def sync():
   with patch('rebalance.ingest.config.get_pulse_config',return_value=mismatch):
    r=_refresh_sync(p/'unused.db',dry_run=True);assert r['error'] and r['dry_run']
  check('real sync identity mismatch returns structured error',sync)
  def doctor():
   with patch('rebalance.doctor._scheduler_policy_jobs',return_value=['pulse-sync']),patch('rebalance.ingest.config.get_pulse_config',return_value=mismatch):
    r=_check_scheduler_liveness(launchctl_output='',agents_dir=p);assert any(x.status=='error' and 'fleet configuration' in x.name for x in r);assert any(x.status=='error' and x.name=='scheduler:pulse-sync' for x in r)
  check('real scheduler identity error preserves unloaded-job failure',doctor)
  collector.unlink()
  def fleet_doctor():
   with patch('rebalance.ingest.pulse_health.read_collector_health',return_value=[]),patch('rebalance.ingest.config.get_pulse_config',return_value=mismatch):
    r=_check_pulse_collectors();assert any(x.status=='error' and 'fleet configuration' in x.name for x in r)
  check('real missing collector file yields doctor config failure',fleet_doctor)
if failed:raise SystemExit(1)
