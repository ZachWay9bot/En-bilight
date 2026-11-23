#!/usr/bin/env python3
# VU-Ambilight V1R10R4: optional large-contrast 2-4 frame guard. Minimal Python dependencies: os/time only.
# This module never accesses hardware. The input is V1R9 RGB, not changed by default calibration.
import os
import time

BASE=os.environ.get('VU_AMBILIGHT_HOME','/home/en-bilight')
CFG=BASE+'/settings.cfg'
RUNTIME=os.environ.get('VU_AMBILIGHT_RUNTIME','/tmp/en-bilight')
STATUS=RUNTIME+'/live_status.txt'
DEFAULT={
    'delay_ms':80, 'smooth_pct':18, 'deadband':2,
    'brightness':54,
    'flash_guard_frames':1, 'flash_guard_delta':100,
    'top_pct':3, 'right_pct':2, 'bottom_pct':3, 'left_pct':2,
    'red_pct':100, 'green_pct':100, 'blue_pct':100,
    'saturation_pct':100, 'gamma_red':100, 'gamma_green':100, 'gamma_blue':100
}
LIMITS={
    'delay_ms':(0,500), 'smooth_pct':(0,95), 'deadband':(0,64),
    'brightness':(1,255),
    'flash_guard_frames':(1,4), 'flash_guard_delta':(40,220),
    'top_pct':(1,50), 'right_pct':(1,50), 'bottom_pct':(1,50), 'left_pct':(1,50),
    'red_pct':(40,160), 'green_pct':(40,160), 'blue_pct':(40,160),
    'saturation_pct':(50,300), 'gamma_red':(60,300), 'gamma_green':(60,300), 'gamma_blue':(60,300)
}

def validate(cfg):
    if set(cfg)!=set(DEFAULT):raise ValueError('Unbekannter oder fehlender Parameter')
    result={}
    for k in DEFAULT:
        try: v=int(cfg[k])
        except (ValueError,TypeError):raise ValueError('Ungueltige Zahl: '+k)
        low,high=LIMITS[k]
        if not low<=v<=high:raise ValueError('%s ausserhalb %s..%s'%(k,low,high))
        result[k]=v
    return result

def load(path=CFG):
    cfg=DEFAULT.copy()
    try:
        with open(path,'r') as f:
            for line in f:
                line=line.strip()
                if not line or line.startswith('#') or '=' not in line:continue
                k,v=line.split('=',1)
                if k in cfg:cfg[k]=int(v.strip())
        return validate(cfg)
    except FileNotFoundError:
        return DEFAULT.copy()

def save(cfg,path=CFG):
    cfg=validate(cfg)
    folder=os.path.dirname(path)
    if not os.path.isdir(folder):os.makedirs(folder)
    target=path+'.new'
    with open(target,'w') as f:
        f.write('# VU-Ambilight V1R10: 100 = RAW / neutral for gains, saturation and gamma\n')
        for k in DEFAULT:f.write('%s=%d\n'%(k,cfg[k]))
        f.flush()
        os.fsync(f.fileno())
    os.replace(target,path)

def clamp(v):
    return 0 if v<0 else (255 if v>255 else v)

class FlashGuard:
    """Holds ONLY large per-LED brightness jumps until they persist N frames.
    Neutral (1 frame) returns source bytes unchanged. No independent gamma,
    saturation or spatial mixing. Intended to remove A-B-A single-frame flashes.
    A confirmed hard cut is delayed (N-1) * 40 ms at nominal 25 fps.
    """
    def __init__(self, cfg):
        self.cfg=cfg
        self.stable=None
        self.streak=[]
        self.dirs=[]
        self.held=0
        self.confirmed=0
    def change(self, cfg):
        if cfg!=self.cfg:
            self.cfg=cfg
            self.stable=None
            self.streak=[0]*314
            self.dirs=[0]*314
            return True
        return False
    def apply(self, raw):
        if len(raw)<3 or len(raw)%3:raise ValueError('RGB muss 3 Bytes pro LED haben')
        if self.stable is not None and len(self.stable)!=len(raw):
            self.stable=None;self.streak=[];self.dirs=[]
        n=self.cfg['flash_guard_frames']
        if n<=1:
            return raw  # byte-identical RAW path
        if self.stable is None:
            self.stable=bytearray(raw)
            self.streak=[0]*(len(raw)//3);self.dirs=[0]*(len(raw)//3)
            return raw
        threshold=self.cfg['flash_guard_delta']
        out=self.stable
        streak=self.streak;direction=self.dirs
        for i in range(len(raw)//3):
            j=3*i
            r=raw[j];g=raw[j+1];b=raw[j+2]
            old=(77*out[j]+150*out[j+1]+29*out[j+2])>>8
            new=(77*r+150*g+29*b)>>8
            d=new-old
            if abs(d)<threshold:
                # small/gradual changes are always immediate
                out[j]=r;out[j+1]=g;out[j+2]=b
                streak[i]=0;direction[i]=0
            else:
                sign=1 if d>0 else -1
                if sign==direction[i]:
                    streak[i]+=1
                else:
                    direction[i]=sign;streak[i]=1
                if streak[i]>=n:
                    out[j]=r;out[j+1]=g;out[j+2]=b
                    streak[i]=0;direction[i]=0
                    self.confirmed+=1
                else:
                    self.held+=1
        return bytearray(out)

class Effects:
    def __init__(self,config=None):
        self.cfg=validate(config or DEFAULT.copy())
        self.prev=None
        self.luts=None
        self.rebuild()
    def rebuild(self):
        c=self.cfg
        self.neutral=all(c[k]==100 for k in ('red_pct','green_pct','blue_pct','saturation_pct','gamma_red','gamma_green','gamma_blue'))
        gains=(c['red_pct'],c['green_pct'],c['blue_pct'])
        gammas=(c['gamma_red'],c['gamma_green'],c['gamma_blue'])
        luts=[]
        for gain,gamma in zip(gains,gammas):
            lut=[]
            for value in range(256):
                v=min(255,value*gain/100.0)
                if gamma != 100:v=255.0*((v/255.0)**(gamma/100.0))
                lut.append(clamp(int(v+0.5)))
            luts.append(bytes(lut))
        self.luts=tuple(luts)
    def change(self,config):
        config=validate(config)
        if config!=self.cfg:
            self.cfg=config
            self.rebuild()
            self.prev=None
            return True
        return False
    def apply(self,raw):
        if len(raw)<3 or len(raw)%3:raise ValueError('RGB muss 3 Bytes pro LED haben')
        c=self.cfg
        smooth=c['smooth_pct']
        db=c['deadband']
        last=self.prev
        if last is not None and len(last)!=len(raw):last=None
        # Bypass calibration when all parameters are neutral, including the exact reference color values.
        cal=self.luts
        sat=c['saturation_pct']
        output=bytearray(len(raw))
        if self.neutral and not smooth and not db:
            output[:]=raw
        else:
            for i in range(0,len(raw),3):
                r=raw[i];g=raw[i+1];b=raw[i+2]
                if sat!=100:
                    gray=(77*r+150*g+29*b+128)>>8
                    r=clamp((gray*100+(r-gray)*sat+50)//100)
                    g=clamp((gray*100+(g-gray)*sat+50)//100)
                    b=clamp((gray*100+(b-gray)*sat+50)//100)
                r=cal[0][r];g=cal[1][g];b=cal[2][b]
                if last is not None:
                    a=last[i];bb=last[i+1];cc=last[i+2]
                    if abs(r-a)<=db:r=a
                    if abs(g-bb)<=db:g=bb
                    if abs(b-cc)<=db:b=cc
                    if smooth:
                        r=(r*(100-smooth)+a*smooth+50)//100
                        g=(g*(100-smooth)+bb*smooth+50)//100
                        b=(b*(100-smooth)+cc*smooth+50)//100
                output[i]=r;output[i+1]=g;output[i+2]=b
        self.prev=output
        return output

class Reload:
    def __init__(self):
        self.config=load()
        self.effects=Effects(self.config)
        self.last_check=0
        self.last_signature=None
    def check(self,force=False):
        t=time.monotonic()
        if not force and t-self.last_check<0.40:return False
        self.last_check=t
        try:
            st=os.stat(CFG)
            sign=(st.st_mtime,st.st_size)
        except OSError:sign=None
        if sign!=self.last_signature or force:
            cfg=load()
            changed=self.effects.change(cfg)
            self.config=cfg
            self.last_signature=sign
            return changed
        return False

def write_status(data,path=STATUS):
    # In RAM (/tmp), not in flash. Atomic read for the web UI.
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    tmp=path+'.new'
    with open(tmp,'w') as f:
        for key,value in data.items():f.write('%s=%s\n'%(key,value))
    os.replace(tmp,path)

def read_status(path=STATUS):
    d={}
    try:
        with open(path,'r') as f:
            for line in f:
                if '=' in line:
                    k,v=line.strip().split('=',1)
                    if k.isidentifier() and len(v)<128:d[k]=v
    except OSError:pass
    return d
