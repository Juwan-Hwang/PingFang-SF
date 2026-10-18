import csv, json, hashlib, sys, re, collections, time
from fontTools.ttLib import TTFont
from fontTools import subset
U = '/workspace/projects/435d098d-7608-493c-a6d9-ceebc965f641/work/audit/ucd/'
OUT = '/workspace/projects/435d098d-7608-493c-a6d9-ceebc965f641/work/audit/'
FONT = '/workspace/projects/435d098d-7608-493c-a6d9-ceebc965f641/work/out/PingFang-SF-Medium.ttf'
t0 = time.time()
# --- UCD 17
gc = {}
first = None
for line in open(U + 'UnicodeData.txt'):
    p = line.split(';'); cp = int(p[0], 16)
    if p[1].endswith(', First>'): first = cp; continue
    if p[1].endswith(', Last>'):
        for c in range(first, cp + 1): gc[c] = p[2]
        continue
    gc[cp] = p[2]
blocks = []
for line in open(U + 'Blocks.txt'):
    m = re.match(r'([0-9A-F]+)\.\.([0-9A-F]+); (.+)', line)
    if m: blocks.append((int(m[1], 16), int(m[2], 16), m[3].strip()))
font = TTFont(FONT)
cmap = font.getBestCmap()
cps = set(cmap)
rows = []
for a, b, name in blocks:
    asg = [c for c in range(a, b + 1) if c in gc and gc[c] not in ('Cs','Cc')]
    cov = [c for c in asg if c in cps]
    extra = [c for c in cps if a <= c <= b and c not in gc]
    n, k = len(asg), len(cov)
    status = 'full' if n and k == n else ('missing' if k == 0 else 'partial')
    if n == 0: status = 'no-assigned'
    rows.append(dict(start='U+%04X' % a, end='U+%04X' % b, block=name, assigned=n, covered=k,
                     missing=n - k, pct=round(100 * k / n, 1) if n else 0, status=status,
                     unassigned_mapped=len(extra)))
with open(OUT + 'blocks.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
unassigned_mapped = sorted(c for c in cps if c not in gc)
print('blocks done', time.time() - t0)

# --- glyph checks
glyf = font['glyf']; gvar = font['gvar'].variations; order = font.getGlyphOrder()
def ghash(gn):
    g = glyf[gn]
    if g.isComposite():
        s = repr([(c.glyphName, c.x, c.y, getattr(c, 'transform', None)) for c in g.components])
    elif g.numberOfContours == 0:
        s = 'EMPTY'
    else:
        coords, ends, flags = g.getCoordinates(glyf)
        s = repr((list(coords), list(ends), [f & 1 for f in flags]))
    v = gvar.get(gn, [])
    s2 = repr([(sorted(tv.axes.items()), tv.coordinates) for tv in v])
    return hashlib.md5(s.encode()).hexdigest(), hashlib.md5((s + s2).encode()).hexdigest()
hm = font['hmtx'].metrics
rev = collections.defaultdict(list)
for c, g in cmap.items(): rev[g].append(c)
ZW_OK = {'Zs', 'Zl', 'Zp', 'Cc', 'Cf', 'Mn', 'Me', 'Co'}
DI = set(range(0x180B, 0x1810)) | set(range(0xFE00, 0xFE10)) | set(range(0xE0100, 0xE01F0)) | {0x115F, 0x1160, 0x3164, 0xFFA0, 0x034F, 0x17B4, 0x17B5, 0x2800}
empty_bad = []; empty_mn = []
hashes = {}
for gn in order:
    hashes[gn] = ghash(gn)
for gn, cs in rev.items():
    if hashes[gn][0] == hashlib.md5(b'EMPTY').hexdigest():
        for c in cs:
            cat = gc.get(c, 'Cn')
            if c in DI or cat in ('Zs', 'Zl', 'Zp', 'Cc', 'Cf'): continue
            (empty_mn if cat in ('Mn', 'Me', 'Co') else empty_bad).append((c, cat, gn))
notdef_h = hashes['.notdef'][0]
notdef_like = [(c, gn) for gn, cs in rev.items() if gn != '.notdef' and hashes[gn][0] == notdef_h for c in cs]
mapped_to_notdef = [c for c, g in cmap.items() if g == '.notdef']
# duplicates among cmapped glyphs (outline+variation identical, same advance)
grp = collections.defaultdict(list)
for gn in rev:
    if hashes[gn][0] == hashlib.md5(b'EMPTY').hexdigest(): continue
    grp[(hashes[gn][1], hm[gn][0])].append(gn)
dups = {k: v for k, v in grp.items() if len(v) > 1}
dup_saving = sum(len(v) - 1 for v in dups.values())
print('glyph checks', time.time() - t0)

# --- orphans via subsetter closure
opts = subset.Options(); opts.layout_features = ['*']; opts.notdef_outline = True
opts.glyph_names = True; opts.name_IDs = ['*']; opts.retain_gids = False
opts.layout_closure = True
s = subset.Subsetter(opts)
s.populate(unicodes=list(cps))
s._prune_pre_subset(font)
s._closure_glyphs(font)
keep = set(s.glyphs_retained)
orphans = [g for g in order if g not in keep]
print('closure', time.time() - t0)
orph_empty = sum(1 for g in orphans if hashes[g][0] == hashlib.md5(b'EMPTY').hexdigest())
pre = collections.Counter(re.sub(r'[\d._].*$', '', g)[:12] for g in orphans)

pua = sorted(c for c in cps if gc.get(c) == 'Co')
def blk(c):
    for a, b, n in blocks:
        if a <= c <= b: return n
    return 'none'
pua_blocks = collections.Counter(blk(c) for c in pua)
res = dict(
    numGlyphs=len(order), cmap=len(cps), unicode_assigned_total=sum(1 for c, v in gc.items() if v not in ('Cs', 'Co')),
    unassigned_mapped=['U+%04X' % c for c in unassigned_mapped],
    empty_nonspace=[('U+%04X' % c, cat, gn) for c, cat, gn in empty_bad],
    empty_marks_or_pua=len(empty_mn), empty_marks_sample=[('U+%04X' % c, cat) for c, cat, _ in empty_mn[:40]],
    notdef_like=[('U+%04X' % c, gn) for c, gn in notdef_like], mapped_to_notdef=len(mapped_to_notdef),
    dup_groups=len(dups), dup_saving=dup_saving,
    dup_examples=[[('U+%04X' % rev[g][0], g) for g in v] for v in list(dups.values())[:15]],
    orphans=len(orphans), orphans_empty=orph_empty, orphan_prefixes=pre.most_common(30),
    orphan_sample=orphans[:60],
    pua=len(pua), pua_blocks=pua_blocks.most_common(),
    glyphs_shared_by_multiple_cps=sum(1 for v in rev.values() if len(v) > 1),
    cmap_glyphs=len(rev),
)
json.dump(res, open(OUT + 'audit_raw.json', 'w'), indent=1, ensure_ascii=False)
open(OUT + 'orphans.txt', 'w').write('\n'.join(orphans))
print(json.dumps({k: v for k, v in res.items() if k not in ('orphan_sample',)}, ensure_ascii=False)[:6000])
print('total', time.time() - t0)
