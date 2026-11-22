#!/usr/bin/env python3
# VU-Ambilight V1R10R3: per-edge image sample depth. Minimal Python dependencies: os/time only.
# This module never accesses hardware. The input is V1R9 RGB, not changed by default calibration.
import os
import time

BASE=os.environ.get('VU_AMBILIGHT_HOME','/home/elight-addons/vu_ambilight_r10r2')
CFG=BASE+'/settings.cfg'
RUNTIME=os.environ.get('VU_AMBILIGHT_RUNTIME','/tmp/vu_ambilight_r10r2')
STATUS=RUNTIME+'/live_status.txt'
DEFAULT={
    'delay_ms':80, 'smooth_pct':18, 'deadband':2,
    'brightness':54,
    'top_pct':3, 'right_pct':2, 'bottom_pct':3, 'left_pct':2,
    'red_pct':100, 'green_pct':100, 'blue_pct':100,
    'saturation_pct':100, 'gamma_red':100, 'gamma_green':100, 'gamma_blue':100
}
LIMITS={
    'delay_ms':(0,500), 'smooth_pct':(0,95), 'deadband':(0,64),
    'brightness':(1,255),
    'top_pct':(1,50), 'right_pct':(1,50), 'bottom_pct':(1,50), 'left_pct':(1,50),
    'red_pct':(40,160), 'green_pct':(40,160), 'blue_pct':(40,160),
    'saturation_pct':(50,180), 'gamma_red':(60,180), 'gamma_green':(60,180), 'gamma_blue':(60,180)
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
        if len(raw)!=942:raise ValueError('RGB != 942 bytes')
        c=self.cfg
        smooth=c['smooth_pct']
        db=c['deadband']
        last=self.prev
        # Bypass calibration when all parameters are neutral, including the exact reference color values.
        cal=self.luts
        sat=c['saturation_pct']
        output=bytearray(942)
        if self.neutral and not smooth and not db:
            output[:]=raw
        else:
            for i in range(0,942,3):
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
