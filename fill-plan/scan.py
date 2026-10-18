# usage: scan.py URL start end outpickle  -- stream byte range of a multistream bz2 dump, count all chars
import sys,subprocess,bz2,collections,pickle,re,os
url,a,b,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
p=subprocess.Popen(['curl','-s','-r',f'{a}-{b-1}',url],stdout=subprocess.PIPE)
data=p.stdout.read()
MAG=b'BZh9\x31\x41\x59\x26\x53\x59'
s=data.find(MAG); e=data.rfind(MAG)
cnt=collections.Counter(); pos=s; nbytes=0
buf=data[s:e]
while buf:
    d=bz2.BZ2Decompressor()
    try: txt=d.decompress(buf)
    except Exception as ex: 
        nx=buf.find(MAG,1); 
        if nx<0: break
        buf=buf[nx:]; continue
    nbytes+=len(txt)
    cnt.update(txt.decode('utf8','ignore'))
    buf=d.unused_data
pickle.dump((cnt,nbytes,b-a),open(out,'wb'))
print(out,nbytes,len(cnt))
