"""Exercise V2R2 shell updater against a fake VU+ filesystem, preserving all settings."""
import tempfile,subprocess,zipfile,os,shutil
from pathlib import Path
rt=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile('/mnt/data/EN_BILIGHT_STANDALONE_V2R1_DASHBOARD_2026-11-22.zip')
with tempfile.TemporaryDirectory(prefix='en-bilight-mon-install-') as t:
    t=Path(t)
    d=t/'home/en-bilight';d.mkdir(parents=True)
    stage=t/'tmp/en-bilight-sysmon-v2r2';stage.mkdir(parents=True)
    for name in ('index.html','web_r10.py'):
        (d/name).write_bytes(z.read('runtime/'+name))
        (stage/name).write_bytes((rt/'runtime'/name).read_bytes())
    (d/'led_layout.py').write_text('# placeholder')
    (d/'settings.cfg').write_text('brightness=18\ndelay_ms=120\n')
    (d/'web_token.txt').write_text('f'*32+'\n')
    (d/'wled_host.txt').write_text('198.51.100.37\n')
    (d/'led_layout.cfg').write_text('top=100\nright=57\n')
    for state in ('running','stopped'):
        (d/'running').unlink(missing_ok=True)
        if state=='running':(d/'running').write_text('1')
        service="""#!/bin/sh
case "$1" in
status) if [ -f '%s/running' ];then echo STANDALONE_RUNNING;else echo STANDALONE_STOPPED;fi;;
stop) rm -f '%s/running';echo STOPPED;;
start) touch '%s/running';echo STARTED;;
*) exit 1;;
esac
"""%(d,d,d)
        (d/'service.sh').write_text(service)
        # staged shell script rewrites only hard-coded test paths
        for f in ('update_sysmon_v2r2.sh','rollback_sysmon_v2r2.sh'):
            src=(rt/'runtime'/f).read_text()
            src=src.replace('/home/en-bilight',str(d)).replace('/tmp/en-bilight-sysmon-v2r2',str(stage))
            (stage/f).write_text(src)
        orig={p.name:p.read_bytes() for p in (d/'settings.cfg',d/'web_token.txt',d/'wled_host.txt',d/'led_layout.cfg')}
        initial=(d/'index.html').read_bytes(),(d/'web_r10.py').read_bytes()
        def run(script):
            r=subprocess.run(['/bin/sh',str(stage/script)],capture_output=True,text=True)
            assert r.returncode==0,(r.returncode,r.stdout,r.stderr)
            return r.stdout
        assert 'SYSMON_V2R2_OK' in run('update_sysmon_v2r2.sh')
        assert (d/'index.html').read_bytes()==(rt/'runtime/index.html').read_bytes()
        assert (d/'web_r10.py').read_bytes()==(rt/'runtime/web_r10.py').read_bytes()
        assert ((d/'running').exists())==(state=='running')
        assert 'BEREITS_INSTALLIERT' in run('update_sysmon_v2r2.sh')
        # execute real installed rollback; contains staged version's dir paths
        r=subprocess.run(['/bin/sh',str(d/'rollback_sysmon_v2r2.sh')],capture_output=True,text=True)
        assert r.returncode==0,(r.stdout,r.stderr)
        assert (d/'index.html').read_bytes()==initial[0]
        assert (d/'web_r10.py').read_bytes()==initial[1]
        assert ((d/'running').exists())==(state=='running')
        assert all((d/name).read_bytes()==data for name,data in orig.items()),'settings changed'
        print('PASS update/rollback',state)
        # Original backup is preserved intentionally, repeat with same baseline.
print('ALL shell upgrade tests PASS')
