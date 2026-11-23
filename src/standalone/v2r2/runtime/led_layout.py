#!/usr/bin/env python3
# En-bilight standalone LED layout, no external dependencies.
# The original 314-zone layout remains the default; no file is needed until edited.
# SPDX-License-Identifier: GPL-2.0-only
import os
import time

BASE=os.environ.get('VU_AMBILIGHT_HOME','/home/en-bilight')
PATH=BASE+'/led_layout.cfg'
RUN=os.environ.get('VU_AMBILIGHT_RUNTIME','/tmp/en-bilight')
TEST_PATH=RUN+'/led_test.cfg'
MAX_LEDS=480  # 10-byte DDP header + 480*3 RGB = 1450 B (IPv4 safe, no fragmentation)
DEFAULT={'top':100,'right':57,'bottom':100,'left':57,
         'start':'TL','direction':'CW','offset':0}
COUNT_KEYS=('top','right','bottom','left')
CORNER_CHOICES=('TL','TR','BR','BL')
DIRECTION_CHOICES=('CW','CCW')


def validate(layout):
    if set(layout)!=set(DEFAULT):
        raise ValueError('Layout: unvollstaendige oder unbekannte Felder')
    obj={}
    for key in COUNT_KEYS:
        try:value=int(layout[key])
        except (ValueError,TypeError):raise ValueError('Ungueltige Zahl: '+key)
        if not 0<=value<=MAX_LEDS:
            raise ValueError('LED-Zahl ausserhalb 0..%d: %s'%(MAX_LEDS,key))
        obj[key]=value
    n=sum(obj.values())
    if not 1<=n<=MAX_LEDS:
        raise ValueError('Gesamtzahl muss 1..%d sein (aktuell %d)'%(MAX_LEDS,n))
    obj['start']=str(layout['start'])
    obj['direction']=str(layout['direction'])
    if obj['start'] not in CORNER_CHOICES or obj['direction'] not in DIRECTION_CHOICES:
        raise ValueError('Start-Ecke oder Laufrichtung ungueltig')
    try:offset=int(layout['offset'])
    except (ValueError,TypeError):raise ValueError('Ungueltiger Startversatz')
    if not 0<=offset<n:raise ValueError('Startversatz muss 0..%d sein'%(n-1))
    obj['offset']=offset
    return obj


def total(layout):return sum(layout[k] for k in COUNT_KEYS)


def load(path=PATH):
    cfg=DEFAULT.copy()
    try:
        with open(path,'r') as f:
            for line in f:
                line=line.strip()
                if not line or line.startswith('#') or '=' not in line:continue
                key,value=line.split('=',1)
                if key in cfg:cfg[key]=value.strip()
    except FileNotFoundError:pass
    return validate(cfg)


def save(layout,path=PATH):
    layout=validate(layout)
    directory=os.path.dirname(path)
    if not os.path.isdir(directory):os.makedirs(directory)
    tmp=path+'.new'
    with open(tmp,'w') as f:
        f.write('# En-bilight LED layout, physical LED 1 follows start+direction+offset\n')
        for key in DEFAULT:f.write('%s=%s\n'%(key,layout[key]))
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    return layout


def physical_order(layout):
    """Per physical LED: (side, coordinate_along_screen_side_0_to_1).
    CW canonical starts at top-left and goes top/right/bottom/left.
    CCW walks the same perimeter in reverse. Offset rotates the first physical LED.
    """
    cfg=validate(layout)
    items=[]
    for side in COUNT_KEYS:
        count=cfg[side]
        row=[(side,(i+0.5)/count) for i in range(count)]
        # canonical orientation: top left->right; right top->bottom;
        # bottom right->left; left bottom->top.
        items.append(row)
    corner_idx={'TL':0,'TR':1,'BR':2,'BL':3}[cfg['start']]
    seq=[]
    if cfg['direction']=='CW':
        for step in range(4):seq.extend(items[(corner_idx+step)%4])
    else:
        for step in range(4):seq.extend(reversed(items[(corner_idx-1-step)%4]))
    offset=cfg['offset']
    return seq[offset:]+seq[:offset]


def points(layout,depths):
    """One sample/LED, four independently configured edge-strip widths."""
    ratios={side:depths[side+'_pct']/200.0 for side in COUNT_KEYS}
    result=[]
    for side,f in physical_order(layout):
        if side=='top':xy=(f,ratios[side])
        elif side=='right':xy=(1-ratios[side],f)
        elif side=='bottom':xy=(1-f,1-ratios[side])
        else:xy=(ratios[side],1-f)
        result.append((xy,))
    return result


class Watcher:
    def __init__(self,path=PATH):
        self.path=path
        self.layout=load(path)
        self.signature=self._signature()
        self.last_check=0.0
    def _signature(self):
        try:
            st=os.stat(self.path)
            return (st.st_mtime_ns,st.st_size)
        except OSError:return None
    def check(self):
        now=time.monotonic()
        if now-self.last_check<0.4:return False
        self.last_check=now
        new_sig=self._signature()
        if new_sig==self.signature:return False
        try:new_layout=load(self.path)
        except (ValueError,OSError):return False # keep previous valid configuration
        self.signature=new_sig
        if new_layout==self.layout:return False
        self.layout=new_layout
        return True


def write_test(mode,index,count,duration=8,path=TEST_PATH):
    if mode not in ('single','sides','off'):raise ValueError('Testmodus unbekannt')
    if not 1<=duration<=10:raise ValueError('Testdauer nur 1..10 Sekunden')
    if mode=='single' and not 1<=index<=count:raise ValueError('LED-Nummer ausserhalb Bereich')
    directory=os.path.dirname(path)
    if not os.path.isdir(directory):os.makedirs(directory)
    tmp=path+'.new'
    with open(tmp,'w') as f:
        f.write('mode=%s\nindex=%d\ncount=%d\nuntil=%.3f\n'%(mode,index,count,time.time()+duration))
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def read_test(count,path=TEST_PATH):
    try:
        with open(path,'r') as f: fields=dict(line.strip().split('=',1) for line in f if '=' in line)
        if time.time()>=float(fields['until']):return None
        if int(fields['count'])!=count:return None
        mode=fields['mode']
        index=int(fields['index'])
        if mode=='off':return None
        if mode=='single' and 1<=index<=count:return (mode,index)
        if mode=='sides':return (mode,0)
    except (OSError,ValueError,KeyError):pass
    return None


def test_frame(layout,mode,index):
    ordered=physical_order(layout)
    data=bytearray(len(ordered)*3)
    if mode=='single':
        if not 1<=index<=len(ordered):raise ValueError('LED-Index ungueltig')
        data[(index-1)*3]=255
    elif mode=='sides':
        rgb={'top':(200,0,0),'right':(0,200,0),'bottom':(0,0,200),'left':(200,120,0)}
        for i,(side,f) in enumerate(ordered):
            data[i*3:i*3+3]=bytes(rgb[side])
    else:raise ValueError('Testmodus unbekannt')
    return data
