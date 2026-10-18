# compute outline hashes for target and PF TC; save mapping
import hashlib, pickle, sys
from fontTools.ttLib import TTFont, TTCollection
def ghash(font, gname, glyf, hmtx):
    g=glyf[gname]
    try:
        coords, ends, flags = g.getCoordinates(glyf)
    except Exception as e:
        return None
    h=hashlib.md5()
    h.update(repr((list(coords), list(ends), [x&1 for x in flags], hmtx[gname][0])).encode())
    return h.hexdigest()
def allhash(font):
    glyf=font['glyf']; hmtx=font['hmtx']
    return {g: ghash(font,g,glyf,hmtx) for g in font.getGlyphOrder()}
if __name__=='__main__':
    t=TTFont('PingFang-SF/PingFang-SF Medium.ttf', lazy=True)
    th=allhash(t)
    pickle.dump(th, open('target_hash.pkl','wb'))
    c=TTCollection('src/v21/PingFangUI.tahoe.26.4.1.wght.wdth.ttc', lazy=True)
    ph=allhash(c.fonts[1])
    pickle.dump(ph, open('pf21_hash.pkl','wb'))
    tv=set(th.values()); 
    print('pf glyphs in target', sum(1 for v in ph.values() if v in tv), len(ph))
    print(t['avar'].segments)
