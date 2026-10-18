import pickle,collections,re,glob
cm=pickle.load(open('data/cmaps.pkl','rb'))
cur=cm['cur'][0]; shs=cm['shsvf'][0]; th=cm['thhak'][0]
props=collections.defaultdict(dict)
for fn in glob.glob('data/Unihan_*.txt'):
    for l in open(fn,encoding='utf8'):
        if l.startswith('U+'):
            c,k,v=l.rstrip('\n').split('\t',2); props[int(c[2:],16)][k]=v
def blk(c):
    for n,a,b in [('B',0x20000,0x2A6DF),('C',0x2A700,0x2B73F),('D',0x2B740,0x2B81F),('E',0x2B820,0x2CEAF),('F',0x2CEB0,0x2EBEF),('I',0x2EBF0,0x2EE5F),('G',0x30000,0x3134F),('H',0x31350,0x323AF),('J',0x323B0,0x3347F),('CompS',0x2F800,0x2FA1F),('Comp',0xF900,0xFAFF),('URO',0x4E00,0x9FFF),('A',0x3400,0x4DBF)]:
        if a<=c<=b: return n
han=[c for c in props if blk(c) not in (None,'URO','A')]
miss=[c for c in han if c not in cur]
print('han ext/compat total',len(han),'missing',len(miss))
print('cur ext in shs',sum(1 for c in han if c in cur and c in shs),'in th only',sum(1 for c in han if c in cur and c not in shs and c in th))
tags={}
def T(c):
    p=props[c];t=[]
    if 'kUnihanCore2020' in p: t.append('Core2020:'+p['kUnihanCore2020'])
    if 'kIICore' in p: t.append('IICore')
    if 'kIRG_HSource' in p: t.append('H')
    if 'kHKGlyph' in p: t.append('HKGlyph')
    if 'kIRG_MSource' in p: t.append('M')
    if 'kCantonese' in p: t.append('Yue')
    if 'kIRG_TSource' in p: t.append('T'+p['kIRG_TSource'].split('-')[0][1:])
    if 'kIRG_GSource' in p: t.append('G'+re.match(r'G([A-Z0-9]+)',p['kIRG_GSource']).group(1))
    if 'kIRG_JSource' in p: t.append('J'+re.match(r'J([A-Z0-9]+)',p['kIRG_JSource']).group(1))
    if 'kIRG_KSource' in p: t.append('K'+re.match(r'K([A-Z0-9]+)',p['kIRG_KSource']).group(1))
    if 'kTGHZ2013' in p: t.append('TGH')
    if 'kJoyoKanji' in p or 'kJinmeiyoKanji' in p: t.append('JP-joyo/jinmei')
    if 'kFrequency' in p: t.append('freq'+p['kFrequency'])
    if 'kCompatibilityVariant' in p: t.append('compat')
    return t
cnt=collections.Counter()
for c in miss:
    for t in set(T(c)):
        t2=t if not t.startswith(('T','G','J','K')) or t in('TGH',) else t
        cnt[t2]+=1
for k,v in cnt.most_common(80): print(k,v)
pickle.dump((props,miss),open('data/han.pkl','wb'))
