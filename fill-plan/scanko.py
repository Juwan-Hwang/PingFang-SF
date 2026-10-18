import sys,subprocess,bz2,collections,pickle
url,a,b,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
cur=pickle.load(open('data/cmaps.pkl','rb'))['cur'][0]
data=subprocess.run(['curl','-s','-r',f'{a}-{b-1}',url],stdout=subprocess.PIPE).stdout
MAG=b'BZh9\x31\x41\x59\x26\x53\x59'
s=data.find(MAG); e=data.rfind(MAG); buf=data[s:e]
tok=collections.Counter(); df=collections.Counter(); npages=0; nbytes=0
while buf:
    d=bz2.BZ2Decompressor()
    try: txt=d.decompress(buf)
    except Exception:
        nx=buf.find(MAG,1)
        if nx<0: break
        buf=buf[nx:]; continue
    buf=d.unused_data; nbytes+=len(txt)
    t=txt.decode('utf8','ignore'); tok.update(t)
    for page in t.split('<page>'):
        df.update(set(page)); npages+=1
keep=lambda k: ord(k)>0x20 and ord(k) not in cur
pickle.dump(dict(tok=collections.Counter({k:v for k,v in tok.items() if keep(k)}),df=collections.Counter({k:v for k,v in df.items() if keep(k)}),pages=npages,bytes=nbytes),open(out,'wb'))
print(out,nbytes,npages)
