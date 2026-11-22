#!/usr/bin/env python3
"""VU-Ambilight R10 slider-range hotfix for existing R10R3 or R10R4.
No external Python dependencies; changes only two known, exact text fragments.
"""
import os
import sys

FRONT = 'index.html'
BACK = 'effects_r10.py'

HTML_CHANGES = (
    ('id="saturation_pct" type="range" min="50" max="180"',
     'id="saturation_pct" type="range" min="50" max="300"'),
    ('id="gamma_red" type="range" min="60" max="180"',
     'id="gamma_red" type="range" min="60" max="300"'),
    ('id="gamma_green" type="range" min="60" max="180"',
     'id="gamma_green" type="range" min="60" max="300"'),
    ('id="gamma_blue" type="range" min="60" max="180"',
     'id="gamma_blue" type="range" min="60" max="300"'),
)
LIMITS_OLD = "'saturation_pct':(50,180), 'gamma_red':(60,180), 'gamma_green':(60,180), 'gamma_blue':(60,180)"
LIMITS_NEW = "'saturation_pct':(50,300), 'gamma_red':(60,300), 'gamma_green':(60,300), 'gamma_blue':(60,300)"
INFO_OLD = '<small>Gamma 100 = linear/unverändert. Andere Werte werden nur auf Wunsch aktiv.</small>'
INFO_NEW = '<small>Sättigung: 50–300 % (175 % liegt mittig). Gamma: 60–300 / 100 (180 / 100 liegt mittig). Gamma 100 = linear/unverändert. Neue Werte werden erst nach Speichern aktiv.</small>'
TITLE_OLD = '<section class="panel"><h2>Feinabstimmung</h2>'
TITLE_NEW = '<section class="panel"><h2>Feinabstimmung <span style="font-size:11px;color:#78e5cf">Regler erweitert</span></h2>'

def die(msg):
    print('FEHLER: '+msg,flush=True)
    sys.exit(2)

def read(path):
    with open(path,'r',encoding='utf-8') as f:
        return f.read()

def match_version(html):
    versions=[v for v in ('V1R10R3','V1R10R4') if '<title>VU Ambilight · '+v+'</title>' in html]
    if len(versions)!=1:
        die('Nur R10R3 oder R10R4 wird unterstuetzt (keine Aenderung).')
    return versions[0]

def state(directory):
    h=read(os.path.join(directory,FRONT))
    e=read(os.path.join(directory,BACK))
    v=match_version(h)
    status=[]
    for old,new in HTML_CHANGES:
        if h.count(old)==1 and new not in h:status.append('old')
        elif h.count(new)==1 and old not in h:status.append('new')
        else:die('Unbekannte oder doppelte HTML-Regler-Definition: '+old[:34])
    if e.count(LIMITS_OLD)==1 and LIMITS_NEW not in e:status.append('old')
    elif e.count(LIMITS_NEW)==1 and LIMITS_OLD not in e:status.append('new')
    else:die('Unbekannte oder doppelte Backend-Limits (keine Aenderung).')
    if len(set(status))!=1:
        die('UI und Backend haben gemischte Grenzwerte (bitte Snapshot wiederherstellen).')
    if status[0]=='new' and (TITLE_NEW not in h or INFO_NEW not in h):
        die('Erweiterte Regler vorhanden, aber Beschriftungen fehlen (kein Ueberschreiben).')
    if status[0]=='old' and (TITLE_OLD not in h or INFO_OLD not in h):
        die('HTML-Beschriftungen weichen vom erwarteten Original ab (kein Ueberschreiben).')
    return status[0],v,h,e

def write(path,content):
    tmp=path+'.new-r5'
    mode=os.stat(path).st_mode & 0o777
    try:
        with open(tmp,'w',encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp,mode)
        os.replace(tmp,path)
    finally:
        try:os.unlink(tmp)
        except FileNotFoundError:pass

def main():
    if len(sys.argv)==4 and sys.argv[1]=='compatible':
        _,vnow,_,_=state(sys.argv[2])
        _,vbak,_,_=state(sys.argv[3])
        if vnow!=vbak:die('Snapshot '+vbak+' passt nicht zur installierten Version '+vnow)
        print('BACKUP_COMPATIBLE '+vnow)
        return
    if len(sys.argv)!=3 or sys.argv[1] not in ('state','apply','verify','selftest'):
        die('Usage: state|apply|verify|selftest DIRECTORY / compatible INSTALLED BACKUP')
    cmd, directory=sys.argv[1:]
    if cmd=='selftest':
        assert (50+300)/2==175 and (60+300)/2==180
        assert (50<=175<=300 and 60<=180<=300)
        print('SELFTEST PASS: sat 175/300 mittig, Gamma 180/300 mittig')
        return
    current,version,h,e=state(directory)
    if cmd=='state':
        print(current)
        return
    if cmd=='apply':
        if current=='new':
            print('ALREADY_PATCHED '+version)
            return
        new_h=h
        for old,new in HTML_CHANGES:
            new_h=new_h.replace(old,new)
        new_h=new_h.replace(INFO_OLD,INFO_NEW).replace(TITLE_OLD,TITLE_NEW)
        new_e=e.replace(LIMITS_OLD,LIMITS_NEW)
        # Only the expected fields and descriptions may change.
        if new_h==h or new_e==e:die('Keine Aenderung vorgenommen')
        write(os.path.join(directory,FRONT),new_h)
        write(os.path.join(directory,BACK),new_e)
        print('PATCH_APPLIED '+version+' | nur HTML + Limits | Sat 50..300 | Gamma 60..300')
    elif cmd=='verify':
        if current!='new':die('Patch nicht vollstaendig aktiv')
        # Verify the runtime reads the extended bounds. Do NOT write settings.
        sys.path.insert(0,directory)
        import effects_r10
        assert effects_r10.LIMITS['saturation_pct']==(50,300)
        for k in ('gamma_red','gamma_green','gamma_blue'):
            assert effects_r10.LIMITS[k]==(60,300)
        cfg=effects_r10.DEFAULT.copy()
        cfg.update(saturation_pct=175,gamma_red=180,gamma_green=180,gamma_blue=180)
        effects_r10.validate(cfg)
        cfg.update(saturation_pct=300,gamma_red=300,gamma_green=300,gamma_blue=300)
        effects_r10.validate(cfg)
        fx=effects_r10.Effects(cfg)
        x=fx.apply(bytes([10,50,100])*314)
        assert len(x)==942 and all(0<=v<=255 for v in x)
        print('VERIFY_PASS '+version+' | Grenzen und LUT bis 300 geprueft | 314 LEDs | keine Settings geschrieben')

if __name__=='__main__':
    main()
