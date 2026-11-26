"""Second pass: attribute each priced message to Waggle or not, by how much its hour of its file talks about Waggle."""
import json, os, io, zipfile
from pathlib import Path
from collections import defaultdict

HOME = Path.home(); ROOT = HOME / ".claude" / "projects"
PRICE = {
    "claude-fable-5-2": (8, 40, 0.20), "claude-fable-5-1": (10, 50, 1.0), "claude-fable-5": (10, 50, 1.0),
    "claude-opus-5-5": (4, 20, 0.20), "claude-opus-5": (5, 25, 0.5), "claude-opus-4-8": (5, 25, 0.5),
    "claude-opus-4-7": (5, 25, 0.5), "claude-opus-4-6": (5, 25, 0.5),
    "claude-sonnet-5-5": (2, 10, 0.10), "claude-sonnet-5": (2, 10, 0.2), "claude-sonnet-4-6": (3, 15, 0.3),
    "claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-haiku-4-5": (1, 5, 0.1),
}
def pk(model):
    best = None
    for k in PRICE:
        if model.startswith(k) and (best is None or len(k) > len(best)): best = k
    return best

seen = {}                                   # msg id -> [bucket, sess, model, in, out, c5, c1h, cr]
bucket = defaultdict(lambda: [0, 0])        # (file, hour) -> [bytes, waggle mentions]
NOT_WAGGLE = ("81af818b", "944919f4")       # small unrelated chats whose memory index inflates the count

def feed(lines, fkey, skey):
    hour = "?"
    for line in lines:
        o = None
        if b'"timestamp"' in line[:4000] or b'"usage"' in line:
            try: o = json.loads(line)
            except Exception: o = None
        if o and o.get("timestamp"): hour = o["timestamp"][:13]
        b = bucket[(fkey, hour)]; b[0] += len(line); b[1] += line.lower().count(b"waggle")
        if not o or o.get("type") != "assistant": continue
        m = o.get("message") or {}; u = m.get("usage")
        if not u: continue
        cc = u.get("cache_creation") or {}; cw = u.get("cache_creation_input_tokens") or 0
        c1h = cc.get("ephemeral_1h_input_tokens") or 0; c5 = cc.get("ephemeral_5m_input_tokens")
        if c5 is None: c5 = max(0, cw - c1h)
        mid = m.get("id") or o.get("uuid")
        rec = [(fkey, hour), skey, m.get("model") or "", u.get("input_tokens") or 0, u.get("output_tokens") or 0, c5, c1h, u.get("cache_read_input_tokens") or 0]
        old = seen.get(mid)
        if old is None: seen[mid] = rec
        elif rec[4] > old[4]: old[3:] = rec[3:]

for proj in sorted(os.listdir(ROOT)):
    pdir = ROOT / proj
    if not pdir.is_dir(): continue
    for dp, dn, fn in os.walk(pdir):
        for f in fn:
            if not f.endswith(".jsonl"): continue
            p = Path(dp) / f; rel = p.relative_to(pdir).parts
            sid = rel[0][:-6] if len(rel) == 1 else rel[0]
            with open(p, "rb") as fh: feed(fh, str(p), proj + "/" + sid)
arch = HOME / "Claude" / "session-archives"
for dp, dn, fn in os.walk(arch):
    for f in fn:
        if f.endswith(".zip"):
            with zipfile.ZipFile(Path(dp) / f) as z:
                for n in z.namelist():
                    if n.endswith(".jsonl"): feed(io.BytesIO(z.read(n)), f + "::" + n, "ARCHIVE/deleted mission-3 session")

def cost(model, r):
    k = pk(model)
    if not k: return 0.0
    pi, po, pr = PRICE[k]
    return (r[3] * pi + r[4] * po + r[5] * pi * 1.25 + r[6] * pi * 2 + r[7] * pr) / 1e6

tot = defaultdict(float); wag = defaultdict(float); wmodel = defaultdict(lambda: [0.0, 0, 0, 0, 0, 0]); amodel = defaultdict(float)
first = {}
for mid, r in seen.items():
    c = cost(r[2], r); bk = bucket[r[0]]
    proj = r[1].split("/")[0]
    dens = bk[1] / max(bk[0] / 1e6, 0.02)
    is_w = (dens >= 300 or "waggle" in proj.lower() or "wgl" in proj.lower() or proj == "ARCHIVE") and not any(x in r[1] for x in NOT_WAGGLE)
    tot[r[1]] += c; amodel[pk(r[2]) or r[2]] += c
    h = r[0][1]
    if h != "?" and (r[1] not in first or h < first[r[1]]): first[r[1]] = h
    if is_w:
        wag[r[1]] += c; a = wmodel[pk(r[2]) or r[2]]; a[0] += c; a[1] += r[3]; a[2] += r[4]; a[3] += r[5] + r[6]; a[4] += r[7]; a[5] += 1

T = sum(tot.values()); W = sum(wag.values())
print("ALL  $%.2f   WAGGLE $%.2f   messages %d" % (T, W, len(seen)))
print("all by model:", {k: round(v, 2) for k, v in sorted(amodel.items(), key=lambda x: -x[1])})
print("waggle by model: cost, input, output, cache write, cache read, calls")
for k, a in sorted(wmodel.items(), key=lambda x: -x[1][0]): print("  %-20s $%8.2f in %10d out %10d cw %11d cr %13d calls %6d" % (k, *a))
print("waggle tokens total:", sum(a[1] + a[2] + a[3] + a[4] for a in wmodel.values()), "output:", sum(a[2] for a in wmodel.values()))
print("per session (total -> waggle share):")
for k, v in sorted(tot.items(), key=lambda x: -x[1])[:22]:
    print("  %8.2f -> %8.2f  %s  %s" % (v, wag.get(k, 0), first.get(k, "")[:10], k[-40:]))
big = sum(v for k, v in wag.items() if tot[k] >= 5); small = W - big
print("waggle from sessions >= $5: %.2f ; from smaller ones: %.2f" % (big, small))
print("first dated message overall:", min(first.values()), " sessions:", len(tot))
