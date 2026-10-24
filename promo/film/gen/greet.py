import sys
import json, uharfbuzz as hb
from fontTools.ttLib import TTFont
G=[("Hello","Latin","拉丁文"),("你好","Chinese","汉字"),("こんにちは","Japanese kana","日文假名"),("안녕하세요","Hangul","韩文"),
("Γειά σου","Greek","希腊文"),("Привет","Cyrillic","西里尔文"),("مرحبا","Arabic","阿拉伯文"),("नमस्ते","Devanagari","天城文"),
("ਸਤ ਸ੍ਰੀ ਅਕਾਲ","Gurmukhi","古木基文"),("નમસ્તે","Gujarati","古吉拉特文"),("নমস্কার","Bengali","孟加拉文"),("வணக்கம்","Tamil","泰米尔文"),
("ನಮಸ್ಕಾರ","Kannada","卡纳达文"),("നമസ്കാരം","Malayalam","马拉雅拉姆文"),("ନମସ୍କାର","Odia","奥里亚文"),("ආයුබෝවන්","Sinhala","僧伽罗文"),
("สวัสดี","Thai","泰文"),("ສະບາຍດີ","Lao","老挝文"),("မင်္ဂလာပါ","Myanmar","缅甸文"),("ជំរាបសួរ","Khmer","高棉文"),
("བཀྲ་ཤིས་བདེ་ལེགས","Tibetan","藏文"),("Բարեւ","Armenian","亚美尼亚文"),("გამარჯობა","Georgian","格鲁吉亚文"),("ሰላም","Ethiopic","埃塞俄比亚文")]
p=sys.argv[1] if len(sys.argv) > 1 else '../../PingFang-SF Medium.ttf'
cm=TTFont(p,lazy=True).getBestCmap()
face=hb.Face(open(p,'rb').read()); font=hb.Font(face)
ok=True
for s,en,zh in G:
    miss=[c for c in s if c!=' ' and ord(c) not in cm]
    buf=hb.Buffer(); buf.add_str(s); buf.guess_segment_properties(); hb.shape(font,buf)
    nd=sum(1 for i in buf.glyph_infos if i.codepoint==0)
    print(s,en,len(buf.glyph_infos),'missing',miss,'notdef',nd)
    ok&= not miss and nd==0
print('ALL OK',ok)
json.dump([{"s":s,"en":en,"zh":zh} for s,en,zh in G],open('film/data/greet.json','w'),ensure_ascii=False,indent=0)
