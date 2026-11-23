import tempfile,os,sys,time,threading,socket,json,urllib.parse,shutil
from pathlib import Path
BASE=Path(tempfile.mkdtemp(prefix='en-bilight-v2-tests-'))
os.environ['VU_AMBILIGHT_HOME']=str(BASE/'home')
os.environ['VU_AMBILIGHT_RUNTIME']=str(BASE/'tmp')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import led_layout as L
import web_r10 as W
import fast_bcm73625_r10 as E

# 1 LED cfg defaults & exact reference
assert L.load()==L.DEFAULT
assert L.total(L.DEFAULT)==314
assert E.current_points(L.DEFAULT,E.DEFAULT,E.regions_load())==E.points_edge_depth(E.regions_load(),E.DEFAULT)
for corner,dir,first_side in [('TL','CW','top'),('TR','CW','right'),('BR','CW','bottom'),('BL','CW','left'),
                               ('TL','CCW','left'),('TR','CCW','top'),('BR','CCW','right'),('BL','CCW','bottom')]:
    c=dict(L.DEFAULT,start=corner,direction=dir)
    assert L.physical_order(c)[0][0]==first_side,(corner,dir)
for n in [1,2,30,314,480]:
    c=dict(L.DEFAULT,top=n,right=0,bottom=0,left=0,offset=n-1)
    L.save(c)
    assert L.load()==c
    assert len(L.points(c,E.DEFAULT))==n
    frame=E.ddp(bytes(n*3),25)
    assert len(frame)==10+n*3 and frame[8:10]==(3*n).to_bytes(2,'big')
for bad in [dict(L.DEFAULT,top=500),dict(L.DEFAULT,top=0,right=0,bottom=0,left=0),dict(L.DEFAULT,offset=314),dict(L.DEFAULT,direction='TYPO')]:
    try:L.validate(bad);raise AssertionError('Accepted invalid layout '+str(bad))
    except ValueError:pass
L.save(L.DEFAULT)
print('PASS 1: layout validation, original pixel positions, eight start/direction combinations, 1..480 LEDs, DDP length')

# 2 socket API; create socket pairs and call serve synchronously
TOKEN='a'*32
def request(method,path,body='',token=TOKEN):
    s1,s2=socket.socketpair()
    try:
        payload=body.encode()
        q=f'{path}?key={token}'
        raw=(f'{method} {q} HTTP/1.1\r\nHost: device\r\nContent-Length: {len(payload)}\r\n\r\n').encode()+payload
        s1.sendall(raw)
        W.serve(s2,TOKEN)
        s2.close()
        out=b''
        while True:
            buf=s1.recv(10000)
            if not buf:break
            out+=buf
        return int(out.split(b' ',2)[1]),out.split(b'\r\n\r\n',1)[1].decode('utf-8')
    finally:s1.close();s2.close()
status,response=request('GET','/api/led/layout')
assert status==200 and json.loads(response)['total']==314
status,_=request('GET','/api/led/layout',token='wrong');assert status==401
v=dict(L.DEFAULT,top=90,right=60,bottom=90,left=60,start='TR',direction='CCW',offset=17)
status,response=request('POST','/api/led/layout',urllib.parse.urlencode(v))
assert status==200 and L.load()==v
status,response=request('POST','/api/led/layout',urllib.parse.urlencode(dict(v,top=480)))
assert status==400 and L.load()==v
status,response=request('POST','/api/led/layout','top=100')
assert status==400
status,response=request('POST','/api/led/test','mode=single&index=5')
assert status==400 and 'nicht aktiv' in response
W.read_status=lambda: {'running':'1','updated':str(int(time.time()))}
status,response=request('POST','/api/led/test','mode=single&index=5')
assert status==200 and L.read_test(L.total(v))==('single',5)
status,response=request('POST','/api/led/test','mode=sides&index=0')
assert status==200 and L.read_test(L.total(v))==('sides',0)
assert len(L.test_frame(v,'sides',0))==sum(v[k] for k in L.COUNT_KEYS)*3
status,response=request('POST','/api/led/test','mode=off&index=0')
assert status==200 and L.read_test(L.total(v)) is None
print('PASS 2: HTTP 401, read/write LED layout, invalid values rejected, LED test requires live status, test stop')

# 3 dynamic hardware-free live run, verify no second sender, no fixed 314-byte requirement.
L.save(L.DEFAULT)
Path(E.HOSTFILE).write_text('127.0.0.1\n')
class MockCapture:
    def __init__(self):self.cache_slots=3;self.plan_key=None
    def frame_fast1(self,points):
        return bytearray([90,40,20])*len(points),None
    def close(self):pass
class MockSock:
    def __init__(self):self.packets=[]
    def sendto(self,payload,addr):self.packets.append(payload);return len(payload)
    def close(self):pass
original_socket=E.socket.socket
E.Capture=MockCapture
E.brightness=lambda *args: True
fake=MockSock()
E.socket.socket=lambda *args,**kwargs:fake

def changes():
    time.sleep(.85)
    L.save(dict(L.DEFAULT,top=120,right=65,bottom=120,left=65,start='BR',direction='CCW',offset=8))  # 370
    time.sleep(.95)
    L.write_test('single',1,370,2)
    time.sleep(.75)
    L.save(dict(L.DEFAULT,start='TR',direction='CCW')) # shrink to 314
    time.sleep(.75)
    L.write_test('sides',0,314,2)
thread=threading.Thread(target=changes,daemon=True)
thread.start()
try:E.r10_run(5.0,True,False)
finally:E.socket.socket=original_socket;Path(E.HOSTFILE).unlink(missing_ok=True)
thread.join(0.5)
lengths=[len(p) for p in fake.packets]
assert 952 in lengths and 1120 in lengths,(set(lengths),len(lengths)) # 370*3+10
assert all(l in (952,1120) for l in lengths),set(lengths)
assert any(p[10:]==bytes(370*3) for p in fake.packets),'Shrinking old tail not cleared'
assert any(p[10:13]==b'\xff\x00\x00' for p in fake.packets),'Single LED test did not reach output'
assert any(p[10:13] in [bytes((200,0,0)),bytes((0,200,0)),bytes((0,0,200)),bytes((200,120,0))] for p in fake.packets),'Side test did not reach output'
print(f'PASS 3: 5s simulated live: {len(fake.packets)} DDP packets with 314->370->314 LED transition, old tail clear, led test')
shutil.rmtree(BASE)
print('ALL V2 TESTS PASS')
