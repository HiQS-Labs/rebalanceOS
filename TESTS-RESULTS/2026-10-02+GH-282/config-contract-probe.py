from pathlib import Path
from unittest.mock import patch
import os,tempfile
from rebalance.lib.git_ops import fleet_settings,publish_git_paths
from rebalance.ingest.pulse import publish_pulse
from rebalance.ingest.index_ops import _refresh_sync
from rebalance.doctor import _check_scheduler_liveness,_check_pulse_collectors
fail=[]
def check(name,fn):
 try:fn();print('PASS '+name)
 except Exception as e:fail.append(name);print('FAIL '+name+': '+type(e).__name__)
with tempfile.TemporaryDirectory(prefix='gh282-config-') as d:
 p=Path(d);(p/'config.sh').write_text('device_id=fixture\nfleet_mode=true\nsync_repo_dir='+str(p)+'\n')
 cfg={'pulse_fleet_enabled':True,'pulse_device_id':'fixture','pulse_target_path':None,'sync_subdir':'sync'}
 def missing():
  with patch.dict(os.environ,{'GIT_PULSE_CONFIG_DIR':d}),patch('rebalance.ingest.pulse.get_pulse_config',return_value=cfg):
   r=publish_pulse(p/'unused.db');assert not r['ok'] and 'pulse_target_path' in r['error']
 check('missing target returns config result',missing)
 good=dict(cfg,pulse_target_path=str(p))
 def publication():
  with patch('rebalance.ingest.config.get_pulse_config',return_value=good),patch('rebalance.lib.git_ops.fleet_settings',side_effect=ValueError('identity mismatch')),patch('rebalance.lib.git_ops.run_git') as run:
   r=publish_git_paths(p,['owned.md'],'fixture');assert r['git_error'] and not r['committed'] and not r['pushed'];run.assert_not_called()
 check('publisher mismatch returns error before Git',publication)
 def sync():
  with patch('rebalance.ingest.config.get_pulse_config',return_value=good),patch('rebalance.ingest.sync_snapshot.get_device_id',side_effect=ValueError('identity mismatch')):
   r=_refresh_sync(p/'unused.db',dry_run=True);assert r['error'] and r['dry_run']
 check('sync invalid identity returns structured error',sync)
 def doctor():
  with patch('rebalance.doctor._scheduler_policy_jobs',return_value=['pulse-sync']),patch('rebalance.doctor._local_device_id',side_effect=ValueError('identity mismatch')):
   r=_check_scheduler_liveness(launchctl_output='');assert any(x.status=='error' and 'fleet configuration' in x.name for x in r)
 check('scheduler doctor reports invalid fleet identity',doctor)
 def fleet_doctor():
  with patch('rebalance.ingest.pulse_health.read_collector_health',return_value=[]),patch('rebalance.doctor._local_device_id',side_effect=OSError('missing config')):
   r=_check_pulse_collectors();assert any(x.status=='error' and 'fleet configuration' in x.name for x in r)
 check('fleet doctor reports missing config',fleet_doctor)
if fail:raise SystemExit(1)
