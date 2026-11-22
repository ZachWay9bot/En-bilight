#!/usr/bin/env python3
# Small LAN-only web UI, socket based for minimal OpenPLi Python 3.9.
# Not a public webserver. Token required for every endpoint.
import os
import sys
import socket
import time
from effects_r10 import BASE,CFG,DEFAULT,LIMITS,load,save,read_status,validate

ROOT=os.path.dirname(os.path.abspath(__file__))
PORT=8095
TOKENFILE=BASE+'/web_token.txt'

def token_get():
    if not os.path.isdir(BASE):os.makedirs(BASE)
    try:
        with open(TOKENFILE,'r') as f:
            s=f.read().strip()
            if len(s)==32 and all(c in '0123456789abcdef' for c in s):return s
    except OSError:pass
    s=os.urandom(16).hex()
    with os.fdopen(os.open(TOKENFILE,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),'w') as f:f.write(s+'\n')
    return s

def query_decode(s):
    out={}
    for part in s.split('&'):
        if '=' not in part:continue
        key,val=part.split('=',1)
        # Values are numeric or hex token, no URL-decoding necessary.
        if not key or len(key)>40 or len(val)>100:continue
        out[key]=val
    return out

def json_obj(d):
    # All keys and values come from fixed safe numeric parameters and locally generated status.
    parts=[]
    for k,v in d.items():
        if k not in DEFAULT and k not in ('running','updated','frames','sent','fps','changed','ms','over40','max_ms','queue','live','end'):continue
        val=str(v)
        if len(val)>64:continue
        is_number=val.replace('.','',1).replace('-','',1).isdigit()
        parts.append('"'+k+'":'+(val if is_number else '"'+''.join(ch for ch in val if ch.isalnum() or ch in '._-')+'"'))
    return '{'+','.join(parts)+'}'

def respond(conn,code,content,kind='text/plain; charset=utf-8'):
    if isinstance(content,str):content=content.encode('utf-8')
    reason={200:'OK',400:'Bad Request',401:'Unauthorized',404:'Not Found',405:'Method Not Allowed',413:'Payload Too Large',500:'Server Error'}.get(code,'Error')
    hdr=('HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %d\r\nConnection: close\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nX-Frame-Options: DENY\r\n\r\n'%(code,reason,kind,len(content))).encode('ascii')
    conn.sendall(hdr+content)

def request(conn):
    conn.settimeout(2.0)
    buf=b''
    while b'\r\n\r\n' not in buf and len(buf)<8192:
        x=conn.recv(4096)
        if not x:return None
        buf+=x
    if b'\r\n\r\n' not in buf:return None
    header,body=buf.split(b'\r\n\r\n',1)
    lines=header.decode('latin1').split('\r\n')
    parts=lines[0].split(' ')
    if len(parts)<3:return None
    method,target,_=parts
    n=0
    for ln in lines[1:]:
        if ln.lower().startswith('content-length:'):
            try:n=int(ln.split(':',1)[1].strip())
            except ValueError:return None
    if n<0 or n>4096:return (413,'','',b'')
    while len(body)<n:
        x=conn.recv(min(4096,n-len(body)))
        if not x:return None
        body+=x
    path,_,params=target.partition('?')
    return (method,path,query_decode(params),body[:n])

def serve(conn,token):
    req=request(conn)
    if req is None:respond(conn,400,'Malformed request');return
    method,path,qs,body=req
    if method==413:respond(conn,413,'Payload too large');return
    if qs.get('key','')!=token:
        respond(conn,401,'Unauthorized: use the URL shown by 02_START_WEB.cmd')
        return
    if method=='GET' and path in ('/','/index.html'):
        with open(os.path.join(ROOT,'index.html'),'r') as f:html=f.read()
        respond(conn,200,html,'text/html; charset=utf-8')
    elif method=='GET' and path=='/api/config':
        respond(conn,200,json_obj(load()),'application/json; charset=utf-8')
    elif method=='GET' and path=='/api/status':
        d=read_status()
        if d and 'updated' in d:
            try:
                if time.time()-int(d['updated'])>5:d['running']='0'
            except ValueError:d['running']='0'
        respond(conn,200,json_obj(d),'application/json; charset=utf-8')
    elif method=='POST' and path=='/api/config':
        try:
            vals=query_decode(body.decode('ascii'))
            cfg=load()
            if not vals:raise ValueError('Leere Einstellungen')
            for k,v in vals.items():
                if k not in DEFAULT:raise ValueError('Unbekannt: '+k)
                cfg[k]=int(v)
            cfg=validate(cfg)
            save(cfg)
            respond(conn,200,json_obj(cfg),'application/json; charset=utf-8')
        except (ValueError,UnicodeError) as e:
            respond(conn,400,'Ungueltiger Wert: '+str(e))
    else:respond(conn,404,'Not found')

def main():
    token=token_get()
    # We deliberately bind only to LAN-facing interface, not WAN. Firewall/router must not forward this port.
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        server.bind(('0.0.0.0',PORT))
        server.listen(5)
        server.settimeout(1.0)
        print('WEB_READY port=%d token=%s'%(PORT,token),flush=True)
        while True:
            try:conn,addr=server.accept()
            except socket.timeout:continue
            with conn:
                # Only accept local / 192.168.178.0/24 clients, even with token.
                if addr[0]!='127.0.0.1' and not addr[0].startswith('192.168.178.'):
                    try:respond(conn,401,'LAN only')
                    except OSError:pass
                    continue
                try:serve(conn,token)
                except (OSError,ValueError) as e:
                    print('HTTP error %s'%e,flush=True)

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
