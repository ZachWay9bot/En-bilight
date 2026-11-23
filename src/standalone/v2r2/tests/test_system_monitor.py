"""Offline CPU/RAM endpoint, error modes and V2R2 HTML checks."""
import os,sys,io,socket,tempfile,threading,json,time
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parents[1]
os.environ['VU_AMBILIGHT_HOME']=tempfile.mkdtemp(prefix='en-bilight-sysmon-')
os.environ['VU_AMBILIGHT_RUNTIME']=tempfile.mkdtemp(prefix='en-bilight-sysmon-tmp-')
sys.path.insert(0,str(root/'runtime'))
import web_r10 as W

m=W.SystemMetrics()
m.previous=(1000,500);m.previous_at=time.monotonic()-2
m._cpu_counters=lambda:(1200,620)
m._memory=lambda:(20,25,125)
s=m.snapshot()
assert s=={'cpu_pct':40,'ram_pct':20,'ram_used_mb':25,'ram_total_mb':125},s
# Stopped CPU counters must preserve last measured value, no division by zero.
m._cpu_counters=lambda:(1200,620)
assert m.snapshot()['cpu_pct']==40
# /proc disappears or has corrupt data: display unavailable, not zero usage.
def broken():raise OSError('proc unavailable')
m._cpu_counters=broken;m._memory=broken
assert m.snapshot()=={'cpu_pct':-1,'ram_pct':-1,'ram_used_mb':-1,'ram_total_mb':-1}
# Realistic /proc formats and old-kernel fallback.
proc={'/proc/stat':'cpu  120 2 38 800 20 1 2 0 0 0\ncpu0 120 2 38 800 20 1 2 0 0 0\n',
      '/proc/meminfo':'MemTotal: 262144 kB\nMemFree: 32768 kB\nBuffers: 4096 kB\nCached: 65536 kB\n'}
def fake_open(path,*args,**kwargs):
    if path in proc:return io.StringIO(proc[path])
    raise AssertionError(path)
with patch('builtins.open',fake_open):
    assert W.SystemMetrics._cpu_counters()==(983,820)
    rp,ru,rt=W.SystemMetrics._memory()
    assert (rp,ru,rt)==(61,156,256),(rp,ru,rt)
    proc['/proc/meminfo']='MemTotal: 262144 kB\nMemAvailable: 131072 kB\n'
    assert W.SystemMetrics._memory()==(50,128,256)

W.SYSTEM_METRICS.snapshot=lambda:{'cpu_pct':37,'ram_pct':46,'ram_used_mb':119,'ram_total_mb':256}
# Server's existing authenticated endpoint is extended, not duplicated.
first,second=socket.socketpair()
try:
    first.sendall(b'GET /api/status?key=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa HTTP/1.1\r\nHost: test\r\n\r\n')
    W.serve(second,'a'*32)
    second.close()
    out=b''
    while True:
        part=first.recv(8192)
        if not part:break
        out+=part
    assert b'200 OK' in out
    data=json.loads(out.split(b'\r\n\r\n',1)[1].decode())
    assert data['cpu_pct']==37 and data['ram_pct']==46 and data['ram_used_mb']==119
finally:first.close();second.close()
first,second=socket.socketpair()
try:
    first.sendall(b'GET /api/status?key=wrong HTTP/1.1\r\nHost: test\r\n\r\n')
    W.serve(second,'a'*32)
    second.close()
    assert b'401 Unauthorized' in first.recv(1024)
finally:first.close();second.close()

h=(root/'runtime/index.html').read_text()
for label in ('Standalone V2R2','id="sys-cpu"','id="sys-cpu-bar"','id="sys-ram"','id="sys-ram-bar"','id="sys-ram-detail"','renderSystem(s)','setInterval(status,1000)'):
    assert label in h,label
assert h.count('id="sys-ram"')==1
print('PASS: CPU deltas, RAM MemAvailable/fallback, errors, authenticated /api/status and UI bindings')
