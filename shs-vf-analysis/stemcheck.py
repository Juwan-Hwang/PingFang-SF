import numpy as np, freetype, sys
from fontTools.ttLib import TTFont
from stems2 import prof
P=sys.argv[1]
fo=freetype.Face(P); t=TTFont(P,lazy=True); cm=t.getBestCmap()
pairs=[(0x3192,0x4E00,'h'),(0x3193,0x4E8C,'h'),(0x3194,0x4E09,'h'),(0x31D0,0x4E00,'h'),(0x31D1,0x4E28,'v')]
print('wght   ' + '  '.join('%s/%s'%(chr(a),chr(b)) for a,b,_ in pairs))
for w in (100,200,300,400,500,600,700,800,900):
    r=[]
    for a,b,ax in pairs:
        if a not in cm: r.append('  -  '); continue
        sa=prof(fo,t.getGlyphID(cm[a]),(w,100),ax); sb=prof(fo,t.getGlyphID(cm[b]),(w,100),ax)
        r.append('%5.1f/%5.1f'%(sa,sb))
    print(w,'  '.join(r))
