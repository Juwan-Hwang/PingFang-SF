"""Render v1.2.0 fill samples (HarfBuzz shaping via Pillow/libraqm + FreeType) at
wght 100/500/900 and wdth 80/100/120, plus a mixed-script paragraph.

usage: python render_fill.py FONT.ttf OUTDIR
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

ROWS = [
    ('中文 Latin 한국어', '苹方 PingFang SF 대한민국 서울특별시 한국어 위키백과 똠방각하 뷁 햏'),
    ('CJK Ext B–J', '𠀀𡈨𢍏𣡽𤞷𥭣𦸜𧴧𩈉𪃶 𚿶𰟖𰾄\U00032aa1 之乎者也'),
    ('Bengali / Tamil', 'বাংলা ভাষা ক্ষ শ্রী · தமிழ் மொழி ஸ்ரீ சென்னை'),
    ('Malayalam / Kannada / Odia', 'മലയാളം ക്ഷ · ಕನ್ನಡ ಬೆಂಗಳೂರು · ଓଡ଼ିଆ ଭାଷା'),
    ('Sinhala / Thaana / Syriac', 'සිංහල ශ්‍රී ලංකාව · ދިވެހި ބަސް · ܠܫܢܐ ܣܘܪܝܝܐ'),
    ('Armenian / Georgian / Ethiopic', 'Հայերեն Երևան · ქართული თბილისი · አማርኛ አዲስ አበባ'),
    ('Mongolian / Tifinagh / Coptic', 'ᠮᠣᠩᠭᠣᠯ ᠪᠢᠴᠢᠭ · ⵜⴰⵎⴰⵣⵉⵖⵜ · ⲧⲙⲛⲧⲣⲉⲙⲛⲕⲏⲙⲉ'),
    ('Lisu / Tai Le / New Tai Lue / Sundanese', 'ꓡꓲ-ꓢꓴ · ᥖᥭᥰ ᥘᥫᥴ · ᦑᦲᧈᦟᦹᧉ · ᮃᮊ᮪ᮞᮛ ᮞᮥᮔ᮪ᮓ · ꩠꩡꩢ'),
    ('Arabic additions', 'ٻ ڀ ڄ ڃ ڄڄڄ — بسم الله الرحمن الرحيم'),
    ('Math alphanumerics', '𝐇𝐞𝐥𝐥𝐨 𝑯𝒆𝒍𝒍𝒐 𝐻𝑒𝑙𝑙𝑜 𝓗𝓮𝓵𝓵𝓸 𝔥𝔢𝔩𝔩𝔬 𝕙𝕖𝕝𝕝𝕠 𝗛𝗲𝗹𝗹𝗼 𝙷𝚎𝚕𝚕𝚘 𝛂𝛃𝛄'),
    ('Symbols', '⟕䷀䷓䷦䷹ ␠⭢⮃⮟⮸ ␠🀤🙪🞔🞼🠓🡇🡽 𝄂𝄇𝄌𝄪'),
    ('Existing (regression)', 'स्त्री ภาษาไทย ភាសាខ្មែរ မြန်မာ བོད་ཡིག AVATAR Жизнь ΑΥΓΟ'),
]


def font(path, size, w, wd):
    f = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_axes([w, wd])
    return f


def sheet(path, out, w, wd):
    size = 34
    img = Image.new('RGB', (2300, 70 + len(ROWS) * 66), 'white')
    d = ImageDraw.Draw(img)
    lab = font(path, 18, 500, 100)
    d.text((20, 18), 'PingFang SF v1.2.0  wght %d  wdth %d' % (w, wd), font=font(path, 24, 700, 100), fill='black')
    f = font(path, size, w, wd)
    y = 70
    for label, text in ROWS:
        d.text((20, y + 14), label, font=lab, fill=(120, 120, 120))
        d.text((420, y + 48), text, font=f, fill='black', anchor='ls')
        y += 66
    img.save(out)


if __name__ == '__main__':
    path, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    for w in (100, 500, 900):
        sheet(path, os.path.join(outdir, 'fill_w%d.png' % w), w, 100)
    for wd in (80, 120):
        sheet(path, os.path.join(outdir, 'fill_w500_wd%d.png' % wd), 500, wd)
    print('ok')
