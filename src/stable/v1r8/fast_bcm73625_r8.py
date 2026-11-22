#!/usr/bin/env python3
# VU-Ambilight V1R8 - experimental read-only BCM73625 fast sampler.
# Derived from V1R7. No writes to /dev/mem. No autostart/config modifications.
# SPDX-License-Identifier: GPL-2.0-only
import os
import sys
import time
import socket
try:
    import mmap
except ImportError:
    mmap=None

VERSION='V1R8-FAST-SAMPLER'
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
        if key not in self.cache:
            if len(self.cache)>=3:
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

def ddp(rgb,seq):
    need(len(rgb)==942,'DDP 942 bytes erwartet')
    return bytes((0x41,seq&255,1,1,0,0,0,0,3,174))+rgb

def brightness(ip):
    body=b'{"on":true,"bri":54}'
    req=('POST /json/state HTTP/1.1\r\nHost: %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'%(ip,len(body))).encode('ascii')
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((ip,80));s.sendall(req+body)
    except OSError as e:say('WLED Helligkeit nicht gesetzt: %s'%e)
    finally:s.close()

def run_mode(cap,points,samples,duration,live=False):
    name='LIVE' if live else 'PROBE'
    sock=None;ip=None
    if live:
        with open(HOSTFILE,'r') as f:host=f.read().strip()
        need(host and not any(c.isspace() for c in host),'WLED Ziel fehlt')
        ip=socket.gethostbyname(host)
        brightness(ip)
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        say('DDP-Ziel %s:4048 / 314 LEDs / raw RGB / 54 von 255'%ip)
    n=0;changes=0;prev=None;busy=0.0;prints=0
    start=lastprint=time.monotonic();next_time=start
    try:
        while time.monotonic()-start < duration:
            t0=time.monotonic()
            rgb,inf=cap.frame(points)
            busy+=time.monotonic()-t0
            if prev is not None and rgb!=prev:changes+=1
            prev=rgb;n+=1
            if sock:
                sock.sendto(ddp(rgb,n&255),(ip,DDP_PORT))
            now=time.monotonic()
            if now-lastprint>=2.0:
                say('%s %d Punkte/LED: %.1fs, %d Frames (%.1f/s), RGB-Aenderungen %d/%d, Auswertung %.1fms/Bild, Maps %d, Mittel %d/%d/%d'%(
                    name,samples,now-start,n,n/max(0.01,now-start),changes,max(0,n-1),busy*1000/n,cap.remaps,
                    sum(prev[0::3])//NLED,sum(prev[1::3])//NLED,sum(prev[2::3])//NLED))
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
    if n>10 and changes<=1:say('WARNUNG: Bilddaten scheinen eingefroren')
    return fps,changes,n

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
    say('SELFTEST PASS: RGB BT.601 / DDP 952 Bytes / 314 LEDs / 1,2,4 Punkte')

def main(argv):
    if '--selftest' in argv:selftest();return
    need(mmap is not None,'mmap fehlt')
    live='--live' in argv
    need('--probe' in argv or '--sweep' in argv or live,'--probe / --sweep / --live fehlt')
    if live:need('--ack-wled' in argv,'WLED Live nur mit --ack-wled')
    duration=6 if '--sweep' in argv else 15
    if '--seconds' in argv:
        i=argv.index('--seconds');need(i+1<len(argv),'--seconds ohne Wert')
        duration=max(3,min(25,int(argv[i+1])))
    samples=4
    if '--samples' in argv:
        i=argv.index('--samples');need(i+1<len(argv),'--samples ohne Wert')
        samples=int(argv[i+1]);need(samples in (1,2,4),'--samples nur 1,2,4')
    zones=regions_load()
    cap=Capture()
    try:
        if '--sweep' in argv:
            say('A/B/C-Modi ohne WLED: jeweils %.0fs. TV-Szene mit Bewegung waehlen'%duration)
            results=[]
            for cnt in (4,2,1):
                say('BEGIN %d Samples/LED'%cnt)
                points=points_make(zones,cnt)
                r=run_mode(cap,points,cnt,duration,False)
                results.append((cnt,)+r)
            say('--- VERGLEICH ---')
            for cnt,fps,changed,n in results:
                say('%d Punkte: %.2f FPS, veraendert %d/%d'%(cnt,fps,changed,max(0,n-1)))
            good=[cnt for cnt,fps,changes,n in results if fps>=24.0 and changes>=max(2,int(n*.3))]
            if good:say('25-FPS-KANDIDAT: %d Punkte/LED (NUR Probe, noch kein TV/LED-Nachweis)'%max(good))
            else:say('25 FPS noch nicht erreicht. Naechster Weg: nativer MIPS-C-Grabber.')
        else:
            run_mode(cap,points_make(zones,samples),samples,duration,live)
    finally:cap.close()

if __name__=='__main__':
    try: main(sys.argv[1:])
    except KeyboardInterrupt: say('Mit Strg+C gestoppt')
    except (ValueError,OSError,ImportError,IndexError) as e:
        say('ABBRUCH: %s'%e)
        sys.exit(2)
