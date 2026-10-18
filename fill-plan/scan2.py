import sys,subprocess,bz2,collections,pickle,re
url,a,b,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
R=re.compile(open('data/uncov_re.txt').read())
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
    for page in txt.decode('utf8','ignore').split('<page>'):
        f=R.findall(page)
        if f:
            tok.update(f); df.update(set(f))
        npages+=1
pickle.dump(dict(tok=tok,df=df,pages=npages,bytes=nbytes),open(out,'wb'))
print(out,nbytes,npages,len(df))
