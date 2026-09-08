from pathlib import Path
import subprocess,tempfile,hashlib,json,time
root=Path.cwd(); tailer=root/'utils/CLIO/clio-codex-tail.sh'; install=root/'utils/CLIO/INSTALL.md'
source=tailer.read_text(); harness=(root/'test/clio-codex-tail.sh').read_text().split("<<'PYTEST'\n",1)[1].split('\nPYTEST',1)[0]
variants={'candidate':source,'baseline':subprocess.check_output(['git','show','0bffc4d:utils/CLIO/clio-codex-tail.sh'],text=True)}
for name,old,new in [
 ('allow-child','if child or line_start < offset:', 'if line_start < offset:'),
 ('reject-all','if child or line_start < offset:', 'if True:'),
 ('bypass-cutoff','if since is not None and instant < since:', 'if False:'),
 ('partial-cutoff-bypass','if since is not None and instant < since:', 'if offset == 0 and since is not None and instant < since:'),
 ('legacy-reset-bypass','[ "$cached_since" != legacy ] || cached_since="$CAPTURE_SINCE"',':')]:
 assert source.count(old)==1, name
 variants[name]=source.replace(old,new)
results=[]
with tempfile.TemporaryDirectory(prefix='clio-gh199-mutations-') as work:
 for name,body in variants.items():
  script=Path(work)/(name+'.sh');script.write_text(body);script.chmod(0o755); start=time.monotonic()
  p=subprocess.run(['python3','-',str(script),str(install)],input=harness,text=True,capture_output=True,timeout=180)
  result={'case':name,'returncode':p.returncode,'seconds':round(time.monotonic()-start,2),'tailer_sha256':hashlib.sha256(body.encode()).hexdigest(),'output':(p.stdout+p.stderr).strip().replace(work,'<mutation-fixture>')}
  results.append(result); print(name,p.returncode,flush=True)
  assert (p.returncode==0)==(name=='candidate'), result
print('All mutation controls behaved as expected; results:', json.dumps(results, indent=2))
