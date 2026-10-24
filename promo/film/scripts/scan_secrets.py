"""Scan (and optionally mask) secrets before anything is committed: captures, transcripts, comps, READMEs.

  python3 scripts/scan_secrets.py .                 # report, exit 1 if anything is found
  python3 scripts/scan_secrets.py --fix session/    # mask in place: keep a short prefix, replace the rest with •
Masked keys stay recognisable on screen ("ohk_35c6edb7••••••••") without being usable. Run it on the whole repo as the
last step before every commit, and on every capture right after recording.
"""
import argparse, os, re, sys

PATTERNS = [
    ('omni2api key', r'ohk_[A-Za-z0-9]{12,}'),
    ('OpenAI/Anthropic key', r'sk-(?:ant-|proj-)?[A-Za-z0-9_\-]{20,}'),
    ('GitHub token', r'gh[pousr]_[A-Za-z0-9]{20,}'),
    ('GitHub fine-grained', r'github_pat_[A-Za-z0-9_]{30,}'),
    ('AWS key id', r'AKIA[0-9A-Z]{16}'),
    ('Slack token', r'xox[abprs]-[A-Za-z0-9\-]{10,}'),
    ('Google API key', r'AIza[0-9A-Za-z_\-]{30,}'),
    ('Bearer JWT', r'Bearer\s+eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}'),
    ('private key', r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    ('assigned secret', r'(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{24,}'),
]
SKIP_DIRS = {'.git', 'node_modules', 'frames', 'out', '__pycache__'}
TEXT_EXT = {'.py', '.sh', '.js', '.ts', '.html', '.css', '.md', '.txt', '.json', '.ans', '.sse', '.log', '.out', '.cast', '.typescript', '.yaml', '.yml', '.toml', '.svg', '.csv', ''}


def mask(m):
    s = m.group(0); keep = min(12, max(4, len(s) // 4))
    return s[:keep] + '•' * max(8, len(s) - keep)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('paths', nargs='+'); ap.add_argument('--fix', action='store_true')
    a = ap.parse_args(); hits = 0
    for root0 in a.paths:
        walk = [(os.path.dirname(root0), [], [os.path.basename(root0)])] if os.path.isfile(root0) else os.walk(root0)
        for root, dirs, files in walk:
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in files:
                p = os.path.join(root, fn)
                if os.path.splitext(fn)[1].lower() not in TEXT_EXT or not os.path.isfile(p) or os.path.getsize(p) > 5_000_000: continue
                try: s = open(p, encoding='utf-8').read()
                except (UnicodeDecodeError, OSError): continue
                new = s
                for name, pat in PATTERNS:
                    for m in re.finditer(pat, s):
                        if '•' in m.group(0) or 'xxxx' in m.group(0).lower(): continue
                        hits += 1; ln = s.count('\n', 0, m.start()) + 1
                        print(f'{p}:{ln}: {name}: {m.group(0)[:10]}…')
                    if a.fix: new = re.sub(pat, lambda m: m.group(0) if '•' in m.group(0) else mask(m), new)
                if a.fix and new != s: open(p, 'w', encoding='utf-8').write(new); print('masked', p)
    print(f'{hits} finding(s)')
    sys.exit(1 if hits and not a.fix else 0)


if __name__ == '__main__':
    main()
