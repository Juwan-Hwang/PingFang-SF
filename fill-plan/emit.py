import pickle,json,collections
L=pickle.load(open('data/condensed.pkl','rb'))
cm=pickle.load(open('data/cmaps.pkl','rb')); P1,P2=pickle.load(open('data/plang.pkl','rb'))
pret=cm['pret'][0]
SC=json.load(open('data/script_costs.json'))
W='/workspace/projects/435d098d-7608-493c-a6d9-ceebc965f641/work/'
F={'pret':W+'addfont/src/pretendard/public/variable/PretendardVariable.ttf','notokr':W+'addfont/src/gf/NotoSansKR[wght].ttf',
   'pl1':W+'fillplan/src/PlangothicP1-Regular.ttf','pl2':W+'fillplan/src/PlangothicP2-Regular.ttf',
   'notosans':W+'addfont/src/gf/NotoSans[wdth,wght].ttf','sym2':W+'addfont/src/gf/NotoSansSymbols2-Regular.ttf',
   'applesym':W+'addfont/src/osf/Apple Symbols.ttf','segoe':W+'addfont/src/osf/seguisym6_24.ttf',
   'sfarabic':W+'addfont/src/apple/SF-Arabic/SF-Arabic.ttf','notoarabic':W+'addfont/src/gf/NotoSansArabic[wdth,wght].ttf',
   'mongol':W+'addfont/src/osf/NotoSansMongolian-Regular.ttf','lisu':W+'addfont/src/gf/NotoSansLisu[wght].ttf','ntl':W+'addfont/src/gf/NotoSansNewTaiLue[wght].ttf',
   'taile':W+'addfont/src/gf/NotoSansTaiLe-Regular.ttf','myanmar':W+'addfont/src/gf/NotoSansMyanmar[wdth,wght].ttf',
   'mathhybrid':'addfont hybrid: work/src/sf SF Pro VF (sans), addfont/src/apple/NY (serif), addfont/src/apple/SF-Mono + osf/SFNSMono.ttf (mono), addfont/src/osf/STIXTwoMath.otf (script/fraktur/double-struck) — see addfont/mathhybrid.py'}
from fontTools.ttLib import TTFont
sfa=set(TTFont(F['sfarabic'],lazy=True).getBestCmap()); aps=set(TTFont(F['applesym'],lazy=True).getBestCmap())
def p2src(c):
    if 0x1D360<=c<=0x1D37F: return 'sym2'
    if 0x2E00<=c<=0x2E7F: return 'notosans'
    if (0x4DC0<=c<=0x4DFF or 0x1D300<=c<=0x1D35F or 0x27C0<=c<=0x27EF or 0x2980<=c<=0x29FF) and c in aps: return 'applesym'
    return 'segoe'
VFINFO={'Hangul':'variable (Pretendard wght 45–930)','Han':'STATIC (Plangothic Regular 400; no gvar)','script:Georgian':'variable (SF Georgian wght 1–1000)','script:Armenian':'variable (SF Armenian wght 1–1000)',
 'SFIndia':'variable CFF2 (SF India wght 1–1000) → convert to glyf/gvar','script:Ethiopic':'variable (Kefa III wght 300–800)','NOTOSANS':'variable (Noto Sans wght 100–900)','script:Sinhala':'variable (Noto)','script:Syriac':'variable (Noto)','script:Thaana':'variable (Noto)','script:Sundanese':'variable (Noto)','addfont:P3_lisu':'variable 400–700','addfont:P3_newtailue':'variable 400–700','addfont:P4_myanmar':'variable (Noto)','Arabic additions (per letter)':'variable (SF Arabic / Noto)','addfont:Math alnum':'mostly variable (hybrid)','P2 symbols (addfont)':'static (Supplemental Punct. from Noto Sans VF)'}
SHAPE={'script:Tamil':'Indic tml2: akhn + GPOS marks','script:Malayalam':'Indic mlm2: akhn/pref/pstf/rphf/pres + GPOS','script:Bengali':'Indic bng2: full akhn/rphf/blwf/half/pstf/init/pres + GPOS','script:Kannada':'Indic knd2: rphf/blwf/pres/rclt + GPOS','script:Odia':'Indic ory2: rphf/blwf/pstf/pres + GPOS',
 'script:Sinhala':'Indic sinh: akhn/rphf/vatu/pres + GPOS','script:Syriac':'joining (isol/init/medi/fina/rlig) + marks','script:Thaana':'GPOS marks','script:Sundanese':'USE: marks','addfont:P3_mongolian':'Mongolian: isol/init/medi/fina + FVS1–4 + rlig, vertical','addfont:P3_newtailue':'USE (simple)','addfont:P4_myanmar':'merge into existing mym2 lookups','Arabic additions (per letter)':'add init/medi/fina/isol + mark anchors into existing Arabic GSUB/GPOS (merge_arabic_gsub.py)','script:Tifinagh':'none (optional ligatures)','script:Ethiopic':'none','script:Coptic':'none','script:Georgian':'none','script:Armenian':'liga only','addfont:P3_lisu':'none','addfont:P3_taile':'none'}
tr=[]
for x in L:
    cat=x['cat']; srcmap=collections.defaultdict(list)
    for c in x['cps']:
        if cat.startswith('Hangul'): s='pret' if c in pret else 'notokr'
        elif cat.startswith('Han ') or cat=='Hentaigana': s='pl1' if c in P1 else 'pl2'
        elif cat=='P2 symbols (addfont)': s=p2src(c)
        elif cat in('Latin Ext-D (addfont)','LatinExtE','CyrExt','ToneLetters','CDMExt'): s='notosans'
        elif cat in('Mahjong','Cards','Domino','Chess','GeomExt','ArrowsC','Legacy','Ornamental','CtrlOCR'): s='sym2'
        elif cat=='Alchemical': s='applesym'
        elif cat=='Music': s=W+'fillplan/src/gf/NotoMusic-Regular.ttf'
        elif cat=='Arabic additions (per letter)': s='sfarabic' if c in sfa else 'notoarabic'
        elif cat=='addfont:Math alnum': s='mathhybrid'
        elif cat.startswith('script:'):
            k=cat[7:]; s=W+'fillplan/'+SC[k]['font'] + (f"#{SC[k]['idx']}" if SC[k]['font'].endswith('.ttc') else '')
        elif cat.startswith('addfont:P3') or cat.startswith('addfont:P4'):
            s={'addfont:P3_mongolian':'mongol','addfont:P3_lisu':'lisu','addfont:P3_newtailue':'ntl','addfont:P3_taile':'taile','addfont:P4_myanmar':'myanmar','addfont:P3_yi':W+'addfont/src/gf/NotoSansYi-Regular.ttf','addfont:P3_nushu':W+'addfont/src/gf/NotoSansNushu-Regular.ttf','addfont:P3_miao':W+'addfont/src/gf/NotoSansMiao-Regular.ttf'}[cat]
        else: s='?'
        srcmap[F.get(s,s)].append('%04X'%c)
    vf=VFINFO.get('Hangul' if cat.startswith('Hangul') else 'Han' if (cat.startswith('Han ') or cat=='Hentaigana') else ('SFIndia' if cat in('script:Tamil','script:Malayalam','script:Bengali','script:Kannada','script:Odia') else ('NOTOSANS' if cat in('Latin Ext-D (addfont)','LatinExtE','CyrExt','ToneLetters','CDMExt') else cat)),'')
    tr.append(dict(rank=x['rank'],in_plan=x['IN'],category=cat,evidence_band_per_glyph=x['band'],glyphs=x['glyphs'],cumulative_glyphs=x['cum'],codepoint_count=len(x['cps']),
                   value_per_million_pages=round(x['value']*1e6,3),max_page_df={k:v for k,v in x['maxdf'].items()},variable=vf,shaping=SHAPE.get(cat,'none'),sources={k:v for k,v in srcmap.items()}))
INs=[t for t in tr if t['in_plan']]
json.dump(dict(baseline_glyphs_after_cleanup=50102,baseline_source='work/render_cleanup/step8_report.json glyphs_out',target_glyphs=65435,planned_total=INs[-1]['cumulative_glyphs'] if INs else None,
  weights=dict(zh=0.71,en=0.20,ko=0.04,yue=0.04,classical=0.01),noise_floor_df=dict(zh=0,en=0,ko=1,yue=3,classical=2),
  corpora={'zhwiki':'8×200MB slices of zhwiki-latest multistream (1,836,187 pages, 6.6 GB text)','kowiki':'4 slices (515,306 pages)','enwiki':'2 slices (132,512 pages)','zh_yuewiki':'full (309,190 pages)','zh_classicalwiki':'first 30MB (83,012 pages)'},
  tranches=tr),open('fillplan.json','w'))
print(len(tr),'tranches;',len(INs),'in plan; total',INs[-1]['cumulative_glyphs'])
