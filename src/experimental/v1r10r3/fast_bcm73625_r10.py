#!/usr/bin/env python3
# VU-Ambilight V1R9 - separate experimental BCM73625 fast-path sampler.
# Derived from verified V1R8. NO writes to /dev/mem. No autostart/config changes.
# SPDX-License-Identifier: GPL-2.0-only
import os
import sys
import time
import socket
from effects_r10 import Reload, Effects, DEFAULT, write_status, read_status
try:
    import mmap
except ImportError:
    mmap=None

VERSION='V1R10R3-WEB-EDGE-DEPTH'
ROOT=os.path.dirname(os.path.abspath(__file__))
NLED=314
DDP_PORT=4048
REG_BASE=0x10600000
MEM_DEV='/dev/mem'
HOSTFILE='/home/elight-addons/vu_ambilight/wled_host.txt'

# BT.601 limited range. RAW RGB has no gamma/saturation correction.
YCON=tuple(298*(x-16) for x in range(256))
UG=tuple(-100*(x-128) for x in range(256))
UB=tuple(516*(x-128) for x in range(256))
VR=tuple(409*(x-128) for x in range(256))
VG=tuple(-208*(x-128) for x in range(256))


def say(s):
    print('[%s] %s' % (VERSION,s),flush=True)

def need(condition,reason):
    if not condition: raise ValueError(reason)

def clamp(v):
    return 0 if v<0 else (255 if v>255 else v)

def bt601(y,u,v):
    z=YCON[y]
    return (clamp((z+VR[v]+128)>>8),
            clamp((z+UG[u]+VG[v]+128)>>8),
            clamp((z+UB[u]+128)>>8))

def regions_load():
    result=[]
    with open(os.path.join(ROOT,'led_regions.txt'),'r') as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith('#'):continue
            a=s.split()
            need(len(a)==4,'LED-Eintrag hat nicht 4 Spalten')
            v=tuple(float(x) for x in a)
            need(0<=v[0]<v[1]<=1 and 0<=v[2]<v[3]<=1,'LED-Zone ausserhalb Bild')
            result.append(v)
    need(len(result)==314,'LED Count != 314')
    return result

def points_make(regions,samples):
    need(samples in (1,2,4),'Samples nur 1,2 oder 4')
    if samples==1: rel=((0.5,0.5),)
    elif samples==2: rel=((0.25,0.25),(0.75,0.75))
    else: rel=((0.25,0.25),(0.75,0.25),(0.25,0.75),(0.75,0.75))
    out=[]
    for h0,h1,v0,v1 in regions:
        out.append(tuple((h0+(h1-h0)*a,v0+(v1-v0)*b) for a,b in rel))
    return out

def points_edge_depth(regions, cfg):
    """One pixel per LED. Selected percentage denotes the edge strip WIDTH,
    so the pixel lies at its center: 10%% top means Y=5%% of image height.
    Keeps the along-edge positions and physical 314-LED ordering unchanged.
    Defaults 3/2/3/2 percent are identical to original Hyperion centers.
    """
    need(len(regions)==NLED, 'Regionen fehlen')
    for k in ('top_pct','right_pct','bottom_pct','left_pct'):
        need(1<=cfg[k]<=50,'Ungueltige Abtasttiefe: '+k)
    depths=(cfg['top_pct']/200.0,cfg['right_pct']/200.0,
            cfg['bottom_pct']/200.0,cfg['left_pct']/200.0)
    out=[]
    for i,(h0,h1,v0,v1) in enumerate(regions):
        if i<100: pos=((h0+h1)/2.0,depths[0])
        elif i<157: pos=(1.0-depths[1],(v0+v1)/2.0)
        elif i<257: pos=((h0+h1)/2.0,1.0-depths[2])
        else:pos=(depths[3],(v0+v1)/2.0)
        out.append((pos,))
    return out

EDGE_KEYS=('top_pct','right_pct','bottom_pct','left_pct')

class Capture:
    def __init__(self):
        need(mmap is not None,'Python mmap nicht vorhanden')
        # Refuse operation on wrong chipset rather than reading guessed physical addresses.
        with open('/proc/stb/info/chipset','r') as f: chip=f.read().strip()
        need('73625' in chip,'Falscher Chipsatz: %s'%chip)
        self.fd=os.open(MEM_DEV,os.O_RDONLY | getattr(os,'O_SYNC',0))
        try:
            self.regs=mmap.mmap(self.fd,4096,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ,offset=REG_BASE)
        except BaseException:
            os.close(self.fd);raise
        self.cache={}
        self.cache_slots=3
        self.cache_hits=0
        self.cache_misses=0
        self.remaps=0
        self.plan_key=None
        self.plan=[]
        self.yres=None
        self.yres_cycles=999
    def close(self):
        try:
            for a,b in self.cache.values():a.close();b.close()
            self.cache.clear()
            self.regs.close()
        finally:os.close(self.fd)
    def video_height(self):
        # /proc read only every 32 frames. On geometry changes re-read immediately.
        if self.yres is None or self.yres_cycles>=32:
            with open('/proc/stb/vmpeg/0/yres','r') as f:
                h=int(f.read().strip(),16)
            need(64<=h<=1152,'Videohoehe unplausibel: %d'%h)
            self.yres=h
            self.yres_cycles=0
        self.yres_cycles+=1
        return self.yres
    def info(self):
        r=self.regs
        stride=(r[0x19]<<8)|r[0x18]
        ofs=r[0x3c+24]<<4;ofs2=r[0x3c+28]<<4
        adr=(r[0x37]<<24)|(r[0x36]<<16)|(r[0x35]<<8)
        adr2=(r[0x3c+3]<<24)|(r[0x3c+2]<<16)|(r[0x3c+1]<<8)
        res=self.video_height()
        need(128<=stride<=2048 and stride%16==0,'Stride unplausibel')
        need(res<=ofs<=1216 and ofs%16==0,'Luma Hoehe unplausibel')
        need((res+1)//2<=ofs2<=608 and ofs2%16==0,'Chroma Hoehe unplausibel')
        need(0x01000000<=adr<0xF0000000 and 0x01000000<=adr2<0xF0000000 and adr!=adr2,'Ungueltige Video-Adressen')
        need(adr%256==0 and adr2%256==0,'Unaligned Video-Adresse')
        count=(stride+63)//64
        ly=count*64*ofs+adr%4096
        lc=count*64*ofs2+adr2%4096
        need(ly<=3500000 and lc<=1800000,'Zu grosse Video-Maps')
        return stride,res,ofs,ofs2,adr,adr2,ly,lc
    def get_buffers(self,inf):
        stride,res,ofs,ofs2,adr,adr2,ly,lc=inf
        key=adr,adr2,stride,ofs,ofs2
        if key in self.cache:
            # LRU reinsert, Python 3.9 dict preserves insertion order.
            maps=self.cache.pop(key)
            self.cache[key]=maps
            self.cache_hits+=1
            return maps
        self.cache_misses+=1
        if key not in self.cache:
            if len(self.cache)>=self.cache_slots:
                old=next(iter(self.cache))
                a,b=self.cache.pop(old);a.close();b.close()
            a=mmap.mmap(self.fd,ly,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ,offset=adr-(adr%4096))
            try:
                b=mmap.mmap(self.fd,lc,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ,offset=adr2-(adr2%4096))
            except BaseException:a.close();raise
            self.cache[key]=(a,b)
            self.remaps+=1
        return self.cache[key]
    def frame(self,points):
        inf=self.info()
        stride,res,ofs,ofs2,adr,adr2,ly,lc=inf
        lum,chrom=self.get_buffers(inf)
        plan_key=stride,res,ofs,ofs2,len(points[0])
        if plan_key!=self.plan_key:
            plan=[]
            for pt in points:
                row=[]
                for fx,fy in pt:
                    x=min(stride-1,max(0,int(fx*stride)))
                    y=min(res-1,max(0,int(fy*res)))
                    pair=x&~1
                    yi=(x//64)*(ofs*64)+y*64+((x%64)^3)
                    ui=(pair//64)*(ofs2*64)+(y//2)*64+((pair%64)^3)
                    vi=((pair+1)//64)*(ofs2*64)+(y//2)*64+(((pair+1)%64)^3)
                    row.append((yi,ui,vi))
                plan.append(tuple(row))
            self.plan=plan
            self.plan_key=plan_key
        pl=adr%4096;pc=adr2%4096
        out=bytearray(NLED*3)
        ns=len(points[0])
        # Native physical memory byte loads are expensive. 1/2/4 samples are tested separately.
        for i,group in enumerate(self.plan):
            rr=gg=bb=0
            for yi,ui,vi in group:
                y=lum[pl+yi];u=chrom[pc+ui];v=chrom[pc+vi]
                z=YCON[y]
                rr+=clamp((z+VR[v]+128)>>8)
                gg+=clamp((z+UG[u]+VG[v]+128)>>8)
                bb+=clamp((z+UB[u]+128)>>8)
            o=i*3
            out[o]=(rr+ns//2)//ns
            out[o+1]=(gg+ns//2)//ns
            out[o+2]=(bb+ns//2)//ns
        return out,inf

    def frame_fast1(self,points):
        # Optimized only for 1 sample/LED. Mathematical operations and YUV offsets
        # match the verified V1R8 1-point path byte for byte.
        need(len(points)==NLED and len(points[0])==1,'Fast1 nur mit 1 Punkt/LED')
        inf=self.info()
        stride,res,ofs,ofs2,adr,adr2,ly,lc=inf
        lum,chrom=self.get_buffers(inf)
        plan_key=('FAST1',stride,res,ofs,ofs2)
        if plan_key!=self.plan_key:
            plan=[]
            for pt in points:
                fx,fy=pt[0]
                x=min(stride-1,max(0,int(fx*stride)))
                y=min(res-1,max(0,int(fy*res)))
                pair=x&~1
                yi=(x//64)*(ofs*64)+y*64+((x%64)^3)
                ui=(pair//64)*(ofs2*64)+(y//2)*64+((pair%64)^3)
                vi=((pair+1)//64)*(ofs2*64)+(y//2)*64+(((pair+1)%64)^3)
                plan.append((yi,ui,vi))
            self.plan=plan
            self.plan_key=plan_key
        pl=adr%4096;pc=adr2%4096
        out=bytearray(NLED*3)
        ycon=YCON;vr=VR;ug=UG;vg=VG;ub=UB
        for i,(yi,ui,vi) in enumerate(self.plan):
            y=lum[pl+yi];u=chrom[pc+ui];v=chrom[pc+vi]
            z=ycon[y]
            r=(z+vr[v]+128)>>8
            g=(z+ug[u]+vg[v]+128)>>8
            b=(z+ub[u]+128)>>8
            o=i*3
            out[o]=0 if r<0 else (255 if r>255 else r)
            out[o+1]=0 if g<0 else (255 if g>255 else g)
            out[o+2]=0 if b<0 else (255 if b>255 else b)
        return out,inf

def ddp(rgb,seq):
    need(len(rgb)==942,'DDP 942 bytes erwartet')
    return bytes((0x41,seq&255,1,1,0,0,0,0,3,174))+rgb

def brightness(ip,value=54):
    # WLED official JSON API brightness is 1..255. Don't touch pixel RGB.
    need(1<=value<=255,'WLED Helligkeit 1..255')
    body=('{"on":true,"bri":%d,"udpn":{"send":false}}'%value).encode('ascii')
    req=('POST /json/state HTTP/1.1\r\nHost: %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'%(ip,len(body))).encode('ascii')
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.settimeout(1.5)
    try:
        s.connect((ip,80));s.sendall(req+body)
        response=s.recv(120)
        if b' 200 ' not in response.split(b'\r\n',1)[0]:
            say('WARNUNG: WLED Helligkeit HTTP Antwort: %r'%response[:65])
            return False
        return True
    except OSError as e:
        say('WARNUNG: WLED Helligkeit nicht gesetzt: %s'%e)
        return False
    finally:s.close()

def run_mode(cap,points,samples,duration,live=False,engine="fast"):
    name='LIVE' if live else 'PROBE'
    sock=None;ip=None
    if live:
        with open(HOSTFILE,'r') as f:host=f.read().strip()
        need(host and not any(c.isspace() for c in host),'WLED Ziel fehlt')
        ip=socket.gethostbyname(host)
        brightness(ip)
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        say('DDP-Ziel %s:4048 / 314 LEDs / raw RGB / 54 von 255'%ip)
    need(engine in ('fast','reference'),'Engine unbekannt')
    need(engine!='fast' or samples==1,'Fastpath nur mit 1 Punkt')
    n=0;changes=0;prev=None;busy=0.0;prints=0
    first_last=0.0
    max_frame=0.0
    gap_count=0
    sent=0
    start=lastprint=time.monotonic();next_time=start
    try:
        while time.monotonic()-start < duration:
            t0=time.monotonic()
            if engine=='fast':rgb,inf=cap.frame_fast1(points)
            else:rgb,inf=cap.frame(points)
            elapsed_frame=time.monotonic()-t0
            busy+=elapsed_frame
            if elapsed_frame>max_frame:max_frame=elapsed_frame
            if elapsed_frame>0.04:gap_count+=1
            if prev is not None and rgb!=prev:changes+=1
            prev=rgb;n+=1
            if sock:
                sent_bytes=sock.sendto(ddp(rgb,n&255),(ip,DDP_PORT))
                need(sent_bytes==952,'DDP-Senden unvollstaendig')
                sent+=1
            now=time.monotonic()
            if now-lastprint>=2.0:
                say('%s %d Punkte/LED: %.1fs, %d Frames (%.1f/s), RGB-Aenderungen %d/%d, Auswertung %.1fms/Bild, Maps %d, Mittel %d/%d/%d'%(
                    name,samples,now-start,n,n/max(0.01,now-start),changes,max(0,n-1),busy*1000/n,cap.remaps,
                    sum(prev[0::3])//NLED,sum(prev[1::3])//NLED,sum(prev[2::3])//NLED))
                say('CACHE slots=%d, hits=%d, misses=%d, Ausreisser>40ms=%d, max_frame=%.1fms, DDP_sends=%d'%(
                    cap.cache_slots,cap.cache_hits,cap.cache_misses,gap_count,max_frame*1000,sent))
                lastprint=now;prints+=1
            next_time+=0.04
            pause=next_time-time.monotonic()
            if pause>0:time.sleep(pause)
            else:next_time=time.monotonic()
    finally:
        if sock:sock.close()
    secs=time.monotonic()-start
    fps=n/max(0.001,secs)
    say('ERGEBNIS %d Punkte/LED: %d Bilder / %.2fs = %.2f FPS, verschiedene Uebergaenge %d/%d, Auswertung %.1fms, gesamt Maps %d'%(
        samples,n,secs,fps,changes,max(0,n-1),1000*busy/max(1,n),cap.remaps))
    say('DETAIL engine=%s slots=%d cache_hits=%d misses=%d hitrate=%.1f%% over40ms=%d max=%.1fms DDP=%d'%(
        engine,cap.cache_slots,cap.cache_hits,cap.cache_misses,100*cap.cache_hits/max(1,cap.cache_hits+cap.cache_misses),gap_count,max_frame*1000,sent))
    if n>10 and changes<=1:say('WARNUNG: Bilddaten scheinen eingefroren')
    return fps,changes,n

def selftest_fast1():
    # Synthetic mappings produce identical buffers for old reference and new fast core.
    # No physical memory access. The tests cover black/white, UV saturation, tiling
    # (including next tile), clamping and all 314 LED-region coordinates.
    zones=regions_load()
    points=points_make(zones,1)
    class FakeCapture(Capture):
        def __init__(self,ydata,uvdata):
            self.ydata=ydata;self.uvdata=uvdata
            self.plan_key=None;self.plan=[]
        def info(self):
            # 1920x1080 stride exercises the tested HD geometry.
            stride=1920;res=1080;ofs=1088;ofs2=544
            adr=0x02000000;adr2=0x03000000
            return (stride,res,ofs,ofs2,adr,adr2,3264000,1632000)
        def get_buffers(self,inf):return self.ydata,self.uvdata
    sz_y=(1920//64)*1088*64
    sz_uv=(1920//64)*544*64
    for pattern in range(3):
        if pattern==0:
            ydata=bytes([16])*sz_y
            uvdata=bytes([128])*sz_uv
        elif pattern==1:
            ydata=bytes([235])*sz_y
            uvdata=bytes([128])*sz_uv
        else:
            # varied deterministic Y/U/V bytes, no dependencies
            ydata=bytes(range(256))*(sz_y//256)
            uvdata=(bytes(((i*37+17)&255 for i in range(256))))*(sz_uv//256)
        cap=FakeCapture(ydata,uvdata)
        expected,_=cap.frame(points)
        optimized,_=cap.frame_fast1(points)
        need(expected==optimized,'Fast1-Abweichung zur V1R8 Referenz bei Muster %d'%pattern)
    say('FAST1 SELFTEST PASS: 314 LEDs x 3 HD-Testbilder, bytegenau wie V1R8')

def selftest():
    coords=regions_load()
    need(len(coords)==NLED,'314 LEDs fehlen')
    need(bt601(16,128,128)==(0,0,0),'BT.601 Schwarz falsch')
    need(bt601(235,128,128)==(255,255,255),'BT.601 Weiss falsch')
    for count in (1,2,4):
        points=points_make(coords,count)
        need(len(points)==314 and all(len(row)==count for row in points),'Plan defekt')
        for row in points:
            for x,y in row:need(0<=x<=1 and 0<=y<=1,'Koordinate ungueltig')
    need(len(ddp(bytearray(942),8))==952,'DDP-Laenge falsch')
    selftest_fast1()
    say('SELFTEST PASS: RGB BT.601 / DDP 952 Bytes / 314 LEDs / 1,2,4 Punkte')


def r10_selftest():
    selftest_fast1()
    fx=Effects(dict(DEFAULT,delay_ms=0,smooth_pct=0,deadband=0))
    rgb=bytearray((i*37)&255 for i in range(942))
    need(fx.apply(rgb)==rgb,'Neutral RAW ist nicht bytegenau')
    fx.change(dict(DEFAULT,smooth_pct=18,deadband=2))
    a=fx.apply(bytearray([0])*942)
    b=fx.apply(bytearray([100])*942)
    need(a[0]==0 and b[0]==82,'Leichtes Smoothing fehlerhaft')
    fx.change(dict(DEFAULT,red_pct=150,green_pct=100,blue_pct=100,smooth_pct=0,deadband=0))
    x=fx.apply(bytearray([100,100,100])*NLED)
    need(x[:3]==bytearray([150,100,100]),'RGB Gain fehlerhaft')
    # Original Hyperion region midpoints must be kept with default edge depth.
    regions=regions_load()
    old=points_make(regions,1)
    current=points_edge_depth(regions,DEFAULT)
    for index,(o,n) in enumerate(zip(old,current)):
        # All pixel positions at full HD must be bit identical in truncation.
        for a,b in zip(o[0],n[0]):
            need(int(a*1920)==int(b*1920) and int(a*1080)==int(b*1080),
                 'Default-Sampling verschoben bei LED %d'%index)
    p=points_edge_depth(regions,dict(DEFAULT,top_pct=20,right_pct=10,bottom_pct=30,left_pct=40))
    need(abs(p[0][0][1]-0.10)<1e-10,'Top-Regler fehlerhaft')
    need(abs(p[100][0][0]-0.95)<1e-10,'Rechts-Regler fehlerhaft')
    need(abs(p[157][0][1]-0.85)<1e-10,'Unten-Regler fehlerhaft')
    need(abs(p[257][0][0]-0.20)<1e-10,'Links-Regler fehlerhaft')
    # Ensure 314 channel order and all original along-edge positions retained.
    for i in range(314):
        ax=0 if i<100 or 157<=i<257 else 1
        need(p[i][0][ax]==old[i][0][ax],'LED-Laengsposition veraendert %d'%i)
    say('R10R3 SELFTEST PASS: 314 Originalzonen, RAW RGB, Default-Geometrie, 4 Tiefenregler')

def r10_run(duration,live,daemon=False):
    # Bounded test runs, or continuous persistent service. Read-only /dev/mem.
    if not daemon: need(5<=duration<=180,'Testlauf nur 5..180 Sekunden')
    cfg=Reload()
    cap=Capture();cap.cache_slots=3
    regions=regions_load()
    points=points_edge_depth(regions,cfg.config)
    sock=None;ip=None
    if live:
        with open(HOSTFILE,'r') as f:host=f.read().strip()
        need(host and not any(ch.isspace() for ch in host),'WLED Ziel fehlt')
        ip=socket.gethostbyname(host)
        brightness(ip,cfg.config['brightness'])
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        say('DDP %s:%d | RAW base | 314 LEDs | bri %d/255'%(ip,DDP_PORT,cfg.config['brightness']))
    start=time.monotonic();next_capture=start
    n=0;sent=0;changed=0;prev_raw=None
    cpu_sum=0.0;over40=0;max_ms=0.0;lastprint=start
    q=[];seq=0
    try:
        while daemon or time.monotonic()-start<duration:
            now=time.monotonic()
            if now>=next_capture:
                old_bri=cfg.config['brightness']
                old_edges=tuple(cfg.config[k] for k in EDGE_KEYS)
                if cfg.check():
                    q.clear()
                    if tuple(cfg.config[k] for k in EDGE_KEYS)!=old_edges:
                        # Replan only when percentages changed, not each frame.
                        points=points_edge_depth(regions,cfg.config)
                        cap.plan_key=None
                        say('SAMPLING UPDATE oben=%d%% rechts=%d%% unten=%d%% links=%d%%'%(
                            cfg.config['top_pct'],cfg.config['right_pct'],cfg.config['bottom_pct'],cfg.config['left_pct']))
                    if live and cfg.config['brightness']!=old_bri:
                        brightness(ip,cfg.config['brightness'])
                    say('SETTINGS UPDATE delay=%dms smooth=%d%% deadband=%d RGB=%d/%d/%d bri=%d'%(
                        cfg.config['delay_ms'],cfg.config['smooth_pct'],cfg.config['deadband'],
                        cfg.config['red_pct'],cfg.config['green_pct'],cfg.config['blue_pct'],cfg.config['brightness']))
                t0=time.monotonic()
                rgb,inf=cap.frame_fast1(points)
                t1=time.monotonic()
                dt=t1-t0;cpu_sum+=dt
                if dt>0.04:over40+=1
                if dt*1000>max_ms:max_ms=dt*1000
                if prev_raw is not None and rgb!=prev_raw:changed+=1
                prev_raw=rgb
                out=cfg.effects.apply(rgb)
                n+=1
                if live:
                    q.append((t0+cfg.config['delay_ms']/1000.0,bytes(out)))
                    if len(q)>20:q.pop(0)
                next_capture+=0.04
                if next_capture<time.monotonic()-0.04:next_capture=time.monotonic()
            now=time.monotonic()
            while q and q[0][0]<=now and sock:
                due,payload=q.pop(0)
                sent_bytes=sock.sendto(ddp(payload,seq),(ip,DDP_PORT))
                need(sent_bytes==952,'DDP-Sendefehler')
                seq=(seq+1)&255;sent+=1
                now=time.monotonic()
            if now-lastprint>=2.0:
                passed=now-start
                status={'running':1,'updated':int(time.time()),'frames':n,'sent':sent,
                        'fps':'%.2f'%(n/max(.001,passed)),'changed':changed,
                        'ms':'%.2f'%(1000*cpu_sum/max(1,n)),'over40':over40,
                        'max_ms':'%.1f'%max_ms,'queue':len(q),
                        'delay_ms':cfg.config['delay_ms'],'smooth_pct':cfg.config['smooth_pct'],
                        'top_pct':cfg.config['top_pct'], 'right_pct':cfg.config['right_pct'],
                        'bottom_pct':cfg.config['bottom_pct'], 'left_pct':cfg.config['left_pct'],
                        'deadband':cfg.config['deadband'], 'brightness':cfg.config['brightness'],
                        'live':int(live)}
                write_status(status)
                # Keep persistent-service logs bounded; browser has 2s status updates.
                if not daemon or n<65 or (int(passed)%600<2):
                    say('LIVE=%s %.1fs: %d Frames / %.2f FPS, DDP %d, Rechenzeit %.1fms, >40ms %d, bri=%d'%(live,passed,n,n/max(.001,passed),sent,1000*cpu_sum/max(1,n),over40,cfg.config['brightness']))
                lastprint=now
            tnext=next_capture
            if q and live:tnext=min(tnext,q[0][0])
            pause=tnext-time.monotonic()
            if pause>0:time.sleep(min(0.04,pause))
        elapsed=time.monotonic()-start
        say('ENDE: %d Frames / %.2fs = %.2f FPS, %d/%d RAW-Aenderungen, DDP=%d, %.1f ms Capture, >40ms=%d'%(
            n,elapsed,n/max(.001,elapsed),changed,max(0,n-1),sent,1000*cpu_sum/max(1,n),over40))
        write_status({'running':0,'updated':int(time.time()),'frames':n,'sent':sent,'fps':'%.2f'%(n/max(.001,elapsed)),
                      'changed':changed,'ms':'%.2f'%(1000*cpu_sum/max(1,n)),
                      'over40':over40,'max_ms':'%.1f'%max_ms,'live':int(live),'end':'normal'})
    except BaseException:
        write_status({'running':0,'updated':int(time.time()),'frames':n,'sent':sent,'end':'stopped'})
        raise
    finally:
        if sock:sock.close()
        cap.close()

def main(argv):
    if '--r10-selftest' in argv:r10_selftest();return
    if '--r10-daemon-live' in argv:
        need('--ack-wled' in argv,'Dauerbetrieb braucht --ack-wled')
        r10_run(None,True,True);return
    if '--r10-live' in argv or '--r10-probe' in argv:
        duration=30
        if '--seconds' in argv:
            idx=argv.index('--seconds')
            need(idx+1<len(argv),'--seconds ohne Wert')
            duration=int(argv[idx+1])
        if '--r10-live' in argv:need('--ack-wled' in argv,'Live-Test braucht --ack-wled')
        r10_run(duration,'--r10-live' in argv)
        return
    if '--selftest' in argv:selftest();return
    need(mmap is not None,'mmap fehlt')
    live='--live' in argv
    bench='--bench' in argv
    need('--probe' in argv or bench or live,'--probe / --bench / --live fehlt')
    if live:need('--ack-wled' in argv,'WLED Live nur mit --ack-wled')
    duration=8 if bench else 20
    if '--seconds' in argv:
        i=argv.index('--seconds');need(i+1<len(argv),'--seconds ohne Wert')
        duration=int(argv[i+1]);need(3<=duration<=180,'Dauer nur 3..180 Sekunden')
    if duration>30:need('--ack-long-run' in argv,'Langtest ueber 30s nur mit --ack-long-run')
    samples=1
    if '--samples' in argv:
        i=argv.index('--samples');need(i+1<len(argv),'--samples ohne Wert')
        samples=int(argv[i+1]);need(samples in (1,2,4),'--samples nur 1,2,4')
    need(samples==1,'V1R9 gezielt nur fuer 1 Punkt entwickelt; V1R8 fuer 2/4 behalten')
    engine='fast'
    if '--engine' in argv:
        i=argv.index('--engine');need(i+1<len(argv),'--engine ohne Wert')
        engine=argv[i+1];need(engine in ('fast','reference'),'Engine nur fast/reference')
    slots=3
    if '--cache-slots' in argv:
        i=argv.index('--cache-slots');need(i+1<len(argv),'--cache-slots ohne Wert')
        slots=int(argv[i+1]);need(slots in (3,6),'Cache nur 3 oder 6')
    zones=regions_load()
    cap=Capture()
    try:
        points=points_make(zones,1)
        if bench:
            need(not live,'Benchmark immer ohne WLED')
            say('A/B/C: Referenz 3 Slots, Fastpath 3 Slots, Fastpath 6 Slots. Je %ds; kein WLED'%duration)
            results=[]
            for en,cs in (('reference',3),('fast',3),('fast',6)):
                # close mappings between stages: fair cache comparison, avoid retained stale mappings
                for a,b in cap.cache.values():a.close();b.close()
                cap.cache.clear();cap.remaps=0;cap.cache_hits=0;cap.cache_misses=0
                cap.cache_slots=cs
                cap.plan_key=None
                say('BEGIN engine=%s cache=%d'%(en,cs))
                fps,changes,n=run_mode(cap,points,1,duration,False,en)
                results.append((en,cs,fps,changes,n))
            say('VERGLEICH (TV-Szenen veraendern sich ggf. zwischen Phasen):')
            for en,cs,fps,changes,n in results:
                say('engine=%s cache=%d => %.2f FPS, %d/%d Farbwechsel'%(
                    en,cs,fps,changes,max(0,n-1)))
        else:
            cap.cache_slots=slots
            run_mode(cap,points,1,duration,live,engine)
    finally:cap.close()

if __name__=='__main__':
    try: main(sys.argv[1:])
    except KeyboardInterrupt: say('Mit Strg+C gestoppt')
    except (ValueError,OSError,ImportError,IndexError) as e:
        say('ABBRUCH: %s'%e)
        sys.exit(2)
