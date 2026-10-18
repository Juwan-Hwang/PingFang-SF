import sys; sys.path.insert(0,'.')
from render import *
S=A+'src/'
sd=[(S+'osf/AppleSDGothicNeo.ttc',i,w) for i,w in zip(range(0,18,2),[400,500,600,700,300,100,200,800,900])]
which=sys.argv[1:]
if 'hangul' in which:
    C=[F('Apple SD Gothic Neo (9 static, CFF)',sd),
       F('Pretendard Variable (wght 45–930)',[(S+'pretendard/public/variable/PretendardVariable.ttf',0,0)]),
       F('Noto Sans KR VF (= Source Han Sans K, wght 100–900)',[(S+'gf/NotoSansKR[wght].ttf',0,0)]),
       F('Malgun Gothic (R only here)',[(A+'tmp/malgun6_69.ttf',0,400)])]
    sheet('hangul','P1 Hangul — candidate Hangul inside PingFang SF (Han/Latin/digits = PingFang SF)',C,
      ['한국어 텍스트 和 中文 and English 123','서울특별시 강남구 · 你好 Hello · ㄱㄴㄷㅎ ㉠㈀㉮'])
if 'symbols' in which:
    C=[F('Apple Symbols (static)',[(S+'osf/Apple Symbols.ttf',0,400)],'cap'),
       F('Segoe UI Symbol (static)',[(A+'tmp/seguisym6_24.ttf',0,400)],'cap'),
       F('Noto Sans Symbols 2 (static)',[(S+'gf/NotoSansSymbols2-Regular.ttf',0,400)],'em'),
       F('Noto Sans Math (static)',[(S+'gf/NotoSansMath-Regular.ttf',0,400)],'cap'),
       F('STIX Two Math (static)',[(S+'osf/STIXTwoMath.otf',0,400)],'cap')]
    sheet('symbols','P2 symbols — candidate symbols mixed with PingFang SF / SF Pro (→ ∑ ≤ ★ are PF)',C,
      ['䷀䷁䷂䷃ 乾坤 𝌀𝌆𝌇 𝍠𝍡𝍢 → ∑ ≤ ★ Aa1','⸎⸏⸘⸮ ⬀⬁⬟⬣⭐⮕ ⟀⟁⟐ ⦀⦁⦿⧫ 中文 Text'])
if 'minority' in which:
    pairs=[('Mongolian','ᠮᠣᠩᠭᠣᠯ ᠪᠢᠴᠢᠭ 蒙古文 Mongolian',[F('Noto Sans Mongolian (macOS-bundled, static)',[(S+'gf/NotoSansMongolian-Regular.ttf',0,400)],'em'),F('Mongolian Baiti (Windows, static)',[(A+'tmp/monbaiti5_54.ttf',0,400)],'em')]),
      ('Yi','ꆈꌠꁱꂷ ꀉꂿ 彝文 Yi ꒰꒱',[F('Noto Sans Yi (static)',[(S+'gf/NotoSansYi-Regular.ttf',0,400)],'em'),F('Microsoft Yi Baiti (static)',[(A+'tmp/msyi6_00.ttf',0,400)],'em')]),
      ('Lisu','ꓡꓲ ꓢꓴ ꓫꓬ 傈僳文 Lisu',[F('Noto Sans Lisu VF (wght 400–700)',[(S+'gf/NotoSansLisu[wght].ttf',0,0)],'cap')]),
      ('NewTaiLue','ᦟᦲᧅᦺᦑᦲ 新傣文 Tai Lue',[F('Noto Sans New Tai Lue VF (400–700)',[(S+'gf/NotoSansNewTaiLue[wght].ttf',0,0)],'em'),F('Microsoft New Tai Lue (R/B)',[(A+'tmp/ntailu5_99.ttf',0,400),(A+'tmp/ntailub5_99.ttf',0,700)],'em')]),
      ('TaiLe','ᥖᥭᥰ ᥘᥫᥴ 傣哪文 Tai Le',[F('Noto Sans Tai Le (static)',[(S+'gf/NotoSansTaiLe-Regular.ttf',0,400)],'em'),F('Microsoft Tai Le (R/B)',[(A+'tmp/taile6_00.ttf',0,400),(A+'tmp/taileb6_00.ttf',0,700)],'em')]),
      ('Miao','𖼀𖼁𖼂𖽑𖽒𖾏 苗文 Miao',[F('Noto Sans Miao (static)',[(S+'gf/NotoSansMiao-Regular.ttf',0,400)],'em')]),
      ('Nushu','𛅰𛅱𛅲𛆀𛆁𛇀 女书 Nüshu',[F('Noto Sans Nushu (static)',[(S+'gf/NotoSansNushu-Regular.ttf',0,400)],'em'),F('Noto Traditional Nushu (static)',[(S+'osf/NotoTraditionalNushu-Regular.ttf',0,400)],'em')])]
    for n,ln,C in pairs: sheet('minority_'+n,f'P3 {n} — next to PingFang SF Chinese/Latin',C,[ln],weights=(100,400,900))
if 'math' in which:
    C=[F('STIX Two Math (macOS-bundled)',[(S+'osf/STIXTwoMath.otf',0,400)],'cap'),
       F('Cambria Math',[(S+'osf/cambria6_99.ttc',1,400)],'cap'),
       F('Noto Sans Math',[(S+'gf/NotoSansMath-Regular.ttf',0,400)],'cap'),
       F('Segoe UI Symbol',[(A+'tmp/seguisym6_24.ttf',0,400)],'cap')]
    sheet('mathalnum','P4 Math alphanumerics (social-media "fancy text") next to PingFang SF',C,
      ['𝐇𝐞𝐥𝐥𝐨 𝑯𝒆𝒍𝒍𝒐 𝓗𝓮𝓵𝓵𝓸 𝔥𝔢𝔩𝔩𝔬 ℍ𝕖𝕝𝕝𝕠 你好','𝖧𝖾𝗅𝗅𝗈 𝗛𝗲𝗹𝗹𝗼 𝘏𝘦𝘭𝘭𝘰 𝙷𝚎𝚕𝚕𝚘 𝟏𝟐𝟑 𝛂𝛃 Hello'],weights=(400,700))
if 'p4' in which:
    sheet('latinextd','P4 Latin Ext-D next to PingFang SF (SF Pro) Latin',[F('Noto Sans VF (wght 100–900)',[(S+'gf/NotoSans[wdth,wght].ttf',0,0)],'cap')],['Hꜳꜵꜷ ꝏꝑꝙ ꞌꞍꞒ Ꞵꞵ Aa Hamburg 中'])
    sheet('arabic','P4 Arabic additions (missing letters) beside existing MiSans Arabic in PF',[F('SF Arabic VF (wght 1–1000)',[(S+'apple/SF-Arabic/SF-Arabic.ttf',0,0)],'em'),F('Noto Sans Arabic VF (100–900)',[(S+'gf/NotoSansArabic[wdth,wght].ttf',0,0)],'em')],['العربية ڃ ڊ ڱ ݐ ݑ ࢠ ࢡ ٲ Arabic'],dir=None)
    sheet('myanmar','P4 Myanmar Shan/Mon additions beside existing MiSans Myanmar in PF',[F('Noto Sans Myanmar VF (100–900)',[(S+'gf/NotoSansMyanmar[wdth,wght].ttf',0,0)],'em'),F('Noto Sans Myanmar (macOS ttc, 9 static)',[(S+'osf/NotoSansMyanmar.ttc',i,w) for i,w in [(8,100),(3,200),(4,300),(6,400),(5,500),(7,600),(1,700),(2,800),(0,900)]],'em')],['မြန်မာ ၵႂၢမ်းတႆး ၸႄႈ Myanmar Shan'])
