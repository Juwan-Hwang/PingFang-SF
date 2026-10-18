import pickle,json,collections,math,re
A=pickle.load(open('data/agg.pkl','rb'))
cm=pickle.load(open('data/cmaps.pkl','rb')); cur=cm['cur'][0]
props,_=pickle.load(open('data/han.pkl','rb'))
SC=json.load(open('data/script_costs.json'))
N=json.load(open('../addfont/needs.json'))
W={'zh':0.71,'en':0.20,'ko':0.04,'yue':0.04,'classical':0.01}
NOISE={'zh':0,'en':0,'ko':1,'yue':3,'classical':2}  # list-page floor: yue has 2 pages listing every Ext char (52,575 chars at df=2)
import sys
if len(sys.argv)>1: W.update(json.loads(sys.argv[1]))
BASE=50102; TARGET=65435
def D(L,c): return max(0,A[L]['df'].get(c,0)-NOISE[L])
def P(c):
    return sum(W[L]*D(L,c)/A[L]['pages'] for L in W if A[L]['pages'])
def Pmax(cps):
    return sum(W[L]*max([D(L,c) for c in cps]+[0])/A[L]['pages'] for L in W if A[L]['pages'])
def isks(c):
    try: return len(chr(c).encode('euc_kr'))==2
    except: return False
units=[]  # (key, category, source, cps, glyphs, value, prior)
# --- Hangul syllables: per char. Prior from jamo model on kowiki tokens
ko=A['ko']['tok'] if A['ko']['pages'] else A['zh']['tok']
I=collections.Counter();V=collections.Counter();F=collections.Counter()
for c,n in ko.items():
    if 0xAC00<=c<=0xD7A3:
        s=c-0xAC00; I[s//588]+=n; V[(s%588)//28]+=n; F[s%28]+=n
ti=sum(I.values()) or 1
def jprior(c):
    s=c-0xAC00; return I[s//588]/ti*V[(s%588)//28]/ti*F[s%28]/ti
pret=cm['pret'][0]
for c in range(0xAC00,0xD7A4):
    units.append(('U+%04X'%c,'Hangul KS X 1001' if isks(c) else 'Hangul non-KS','Pretendard VF',[c],1,P(c),(1 if isks(c) else 0, jprior(c))))
for c in N['P1_hangul']:
    if not 0xAC00<=c<=0xD7A3:
        units.append(('U+%04X'%c,'Hangul compat jamo / enclosed','Pretendard VF' if c in pret else 'Noto Sans KR VF',[c],1,P(c),(0,0)))
# --- Han ext per char (Plangothic)
p1=cm.get('pl1'); 
def hanprior(c):
    p=props.get(c,{})
    t=0
    if 'kCantonese' in p: t+=4
    if 'kIRG_TSource' in p: t+=2
    if 'kIRG_GSource' in p and re.match(r'G(GH|4K|BK|CH|CY|FZ|HC|CE|XC|Z\b|ZA|ZH)',p['kIRG_GSource']): t+=1
    if 'kIRG_JSource' in p: t+=1
    if 'kIRG_KSource' in p: t+=0.5
    if 'kIRG_VSource' in p: t+=0.5
    return (0,t)
_,miss=pickle.load(open('data/han.pkl','rb'))
for c in miss:
    blk='Han compat (supplement)' if (0xF900<=c<=0xFAFF or 0x2F800<=c<=0x2FA1F) else 'Han Ext B-J'
    units.append(('U+%04X'%c,blk,'Plangothic P1/P2 (static)',[c],1,P(c),hanprior(c)))
# --- P2 symbols per char
for c in N['P2_symbols']:
    units.append(('U+%04X'%c,'P2 symbols (addfont)','Apple Symbols / Segoe UI Symbol / Noto (addfont split)',[c],1.06,P(c),(0,0)))
for c in N['P4_latinextd']:
    units.append(('U+%04X'%c,'Latin Ext-D (addfont)','Noto Sans VF',[c],1.02,P(c),(0,0)))
# per-char symbol blocks from script_costs
PERCHAR=['Mahjong','Cards','Domino','Chess','GeomExt','ArrowsC','Legacy','Ornamental','Alchemical','CtrlOCR','Music','LatinExtE','ToneLetters','CDMExt','Hentaigana','CyrExt']
for k in PERCHAR:
    d=SC[k]; r=d['glyphs']/max(1,d['have'])
    for c in d['cps']: units.append(('U+%04X'%c,k,d['label'],[c],r,P(c),(0,0)))
# --- whole-script units
WHOLE={k:v for k,v in SC.items() if k not in PERCHAR and k not in ('Bengali-noto','Ethiopic-noto','HangulJamoNoFeat')}
geo=set(SC['Georgian']['cps'])
for k,d in WHOLE.items():
    cps=d['cps'] if k!='Georgian-rest' else [c for c in d['cps'] if c not in geo]
    units.append((k,'script:'+k,d['label'],cps,d['glyphs'] if k!='Georgian-rest' else d['glyphs']-len(d['cps'])+len(cps),Pmax(cps),(0,0)))
import unicodedata as _u
for c in [c for c in N['P4_arabic'] if not 0xFB50<=c<=0xFEFF]:
    units.append(('U+%04X'%c,'Arabic additions (per letter)','SF Arabic VF, else Noto Sans Arabic VF',[c],3.0 if _u.category(chr(c))=='Lo' else 1.0,P(c),(0,0)))
addf={'P3_mongolian':(1537,'Noto Sans Mongolian 3.002 (macOS)'),'P3_yi':(1220,'Noto Sans Yi'),'P3_lisu':(49,'Noto Sans Lisu VF'),'P3_newtailue':(83,'Noto Sans New Tai Lue VF'),'P3_taile':(35,'Noto Sans Tai Le'),'P3_miao':(368,'Noto Sans Miao'),'P3_nushu':(396,'Noto Sans Nushu'),'P4_myanmar':(137,'Noto Sans Myanmar VF')}
for k,(g,src) in addf.items():
    cps=N[k] if k!='P4_arabic' else [c for c in N[k] if not 0xFB50<=c<=0xFEFF]
    units.append((k,'addfont:'+k,src,cps,g,Pmax(cps),(0,0)))
# math alnum by style group (Unicode 1D400 block, 52-letter runs + digits)
ma=sorted(N['P4_mathalnum']); groups=collections.defaultdict(list)
import unicodedata
for c in ma:
    nm=unicodedata.name(chr(c),'')
    st=re.sub(r' (CAPITAL|SMALL|DIGIT).*','',nm).replace('MATHEMATICAL ','')
    groups[st].append(c)
for st,cps in groups.items():
    units.append(('math:'+st,'addfont:Math alnum','SF Pro/New York/SF Mono VF + STIX (addfont hybrid)',cps,len(cps),Pmax(cps),(0,0)))
# greedy by density; ties by prior
def key(u): return (-(u[5]/u[4]), -u[6][0], -u[6][1])
units.sort(key=key)
tot=BASE; rows=[]; totalV=sum(u[5] for u in units)
cumV=0; out_tot=BASE
for u in units:
    fits = tot+u[4] <= TARGET
    if fits: tot+=u[4]; cumV+=u[5]
    out_tot+=u[4]
    rows.append(dict(key=u[0],cat=u[1],src=u[2],cps=u[3],glyphs=u[4],value=u[5],cum=tot if fits else out_tot,cumV=cumV,prior=u[6],IN=fits))
pickle.dump((rows,totalV,W),open('data/ranked.pkl','wb'))
cut=[r for r in rows if r['IN']]
print('units',len(rows),'taken',len(cut),'last cum',cut[-1]['cum'],'value share %.4f'%(cut[-1]['cumV']/totalV))
# category summary inside cut / outside
s=collections.defaultdict(lambda:[0,0,0.0,0,0,0.0])
for r in rows:
    i=0 if r['IN'] else 3
    s[r['cat']][i]+=len(r['cps']); s[r['cat']][i+1]+=r['glyphs']; s[r['cat']][i+2]+=r['value']
for k,v in sorted(s.items(),key=lambda x:-x[1][2]-x[1][5]):
    print(f"{k:34s} IN cps {v[0]:6d} gl {v[1]:7.0f} val {v[2]*1e6:9.1f} | OUT cps {v[3]:6d} gl {v[4]:7.0f} val {v[5]*1e6:9.1f}")
