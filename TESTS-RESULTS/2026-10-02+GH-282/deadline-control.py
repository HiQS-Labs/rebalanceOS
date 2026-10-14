from pathlib import Path
import subprocess,json
baseline=subprocess.check_output(['git','show','bb84cd0:experimental/git-pulse/collect.sh'],text=True)
for name,source,expected,width in [('baseline',baseline,0,1),('fixed',Path('experimental/git-pulse/collect.sh').read_text(),1,2)]:
 lines=source.splitlines();i=next(i for i,x in enumerate(lines) if 'NETWORK_DEADLINE=' in x);command='python3(){ return 6; }; '+ '\n'.join(lines[i:i+width])+'\n';r=subprocess.run(['bash','-c',command],capture_output=True,text=True);print(json.dumps({'source':name,'forcing_command':command,'stdout':r.stdout,'stderr':r.stderr,'exit':r.returncode,'expected':expected}));assert r.returncode==expected
