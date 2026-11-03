import difflib, io, random, time
import streamlit as st
from PIL import Image, ImageDraw
from dnavault import *

st.set_page_config(page_title="DNA Vault", page_icon="🧬", layout="wide")

COL = {"A": (46, 204, 113), "C": (52, 152, 219), "G": (243, 156, 18), "T": (231, 76, 60)}
HEX = {k: "#%02x%02x%02x" % v for k, v in COL.items()}

st.markdown("""
<style>
.hero{padding:28px 32px;border-radius:18px;background:linear-gradient(120deg,#0f2027,#203a43,#2c5364);color:#fff;margin-bottom:18px}
.hero h1{margin:0 0 6px 0;font-size:2.2rem}.hero p{margin:0;opacity:.85;font-size:1.05rem}
.card{border:1px solid rgba(128,128,128,.35);border-radius:14px;padding:16px 18px;height:100%}
.card h4{margin:0 0 6px 0}.card .n{font-size:1.6rem}
.seq{font-family:ui-monospace,Menlo,monospace;font-size:13px;line-height:1.6;word-break:break-all}
.ok{padding:14px 18px;border-radius:12px;background:rgba(46,204,113,.15);border:1px solid #2ecc71}
.bad{padding:14px 18px;border-radius:12px;background:rgba(231,76,60,.15);border:1px solid #e74c3c}
</style>""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🧬 DNA Vault</h1><p>Store a digital file as DNA letters, damage it like a real lab would, '
            'and watch error correction bring it back, bit for bit.</p></div>', unsafe_allow_html=True)


def colored(seq, limit=240):
    s = seq[:limit]
    return "".join(f'<span style="color:{HEX[c]};font-weight:600">{c}</span>' for c in s) + ("…" if len(seq) > limit else "")


def barcode(oligos, rows=60, px=6):
    rows_ = oligos[:rows]
    w = max(map(len, rows_))
    img = Image.new("RGB", (w, len(rows_)), (255, 255, 255))
    for y, o in enumerate(rows_):
        for x, c in enumerate(o):
            img.putpixel((x, y), COL[c])
    return img.resize((w * px // 2, len(rows_) * px), Image.NEAREST)


def sample_image():
    im = Image.new("RGB", (64, 64))
    d = ImageDraw.Draw(im)
    for y in range(64):
        d.line([(0, y), (64, y)], fill=(30 + y * 3, 80, 220 - y * 3))
    d.ellipse([16, 16, 48, 48], fill=(255, 220, 60))
    d.rectangle([28, 28, 36, 36], fill=(20, 20, 60))
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()


def is_image(b):
    try:
        Image.open(io.BytesIO(b)).verify(); return True
    except Exception:
        return False


def show_file(b, caption):
    if is_image(b):
        st.image(b, caption=caption, width=220)
    else:
        st.code(b[:300].decode("utf-8", "replace") + ("…" if len(b) > 300 else ""), language=None)
        st.caption(caption)


def diff_html(a, b, limit=122):
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a[:limit], b[:limit], autojunk=False).get_opcodes():
        seg = b[j1:j2]
        if tag == "equal":
            out.append(f'<span style="opacity:.55">{seg}</span>')
        elif tag == "delete":
            out.append('<span style="background:#e74c3c;color:#fff;padding:0 2px">⌫</span>')
        else:
            out.append(f'<span style="background:#e74c3c;color:#fff;padding:0 2px">{seg}</span>')
    return f'<div class="seq">{"".join(out)}</div>'


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    scheme = st.radio("DNA mapping", ["rotating", "naive"], format_func=lambda s: {
        "rotating": "Rotating (no repeated bases)", "naive": "Naive (2 bits per base)"}[s])
    parity = st.slider("Redundancy: parity oligos per 60", 4, 24, 12)
    cov = st.slider("Reads per oligo (sequencing depth)", 1, 20, 10)
    st.subheader("🧪 Damage")
    p_sub = st.slider("Substitution rate", 0.0, 0.10, 0.01, 0.001, format="%.3f")
    p_ins = st.slider("Insertion rate", 0.0, 0.04, 0.0, 0.001, format="%.3f")
    p_del = st.slider("Deletion rate", 0.0, 0.04, 0.0, 0.001, format="%.3f")
    p_drop = st.slider("Lost oligos (dropout)", 0.0, 0.30, 0.05, 0.01, format="%.2f")
    seed = st.number_input("Random seed", 0, 9999, 1)

tab_how, tab_demo, tab_exp = st.tabs(["📖 How it works", "🚀 Live demo", "📊 Experiments"])

# ------------------------------------------------------------------ how it works
with tab_how:
    st.subheader("Why DNA?")
    st.write("DNA can hold about 1 exabyte per cubic millimetre in theory and lasts thousands of years "
             "when stored dry and cold. This app is a **software simulation** of the idea: nothing is "
             "synthesised in a lab, but the encoding, damage and recovery logic follow how real DNA storage research works.")
    steps = [("1 · Compress", "The file is shrunk with zlib so fewer bases are needed."),
             ("2 · Split & index", "Data is cut into 20-byte pieces. Each gets an index number and a CRC checksum, so it can be put back in order and checked."),
             ("3 · Protect", "Reed–Solomon parity oligos are added. Any lost or corrupted oligos (up to the parity count) can be rebuilt."),
             ("4 · Write as A/C/G/T", "Bytes become bases. Rotating mapping never repeats a base, which avoids long runs that DNA synthesis handles badly."),
             ("5 · Damage", "Synthesis and sequencing cause substitutions, insertions, deletions and lost strands. We read each strand many times."),
             ("6 · Recover", "Reads are voted into a consensus, checked by CRC, missing pieces rebuilt by Reed–Solomon, then the file is verified with SHA-256.")]
    for r in range(0, 6, 3):
        cols = st.columns(3)
        for c, (t, d) in zip(cols, steps[r:r + 3]):
            c.markdown(f'<div class="card"><h4>{t}</h4>{d}</div>', unsafe_allow_html=True)
        st.write("")
    st.subheader("Reading the colours")
    st.markdown(" ".join(f'<span style="background:{HEX[k]};color:#fff;padding:3px 12px;border-radius:8px;font-weight:700">{k}</span>' for k in "ACGT"),
                unsafe_allow_html=True)
    st.caption("Each row of the barcode image in the demo is one DNA strand (oligo); each coloured pixel is one base.")
    st.info("**Limits to remember:** error rates here are illustrative, and the simulator knows which strand each read came from "
            "(real data needs a clustering step). Insertions and deletions are the hardest errors for this decoder.")

# ------------------------------------------------------------------ demo
with tab_demo:
    up = st.file_uploader("Upload a small file (image, text or PDF, up to 200 KB)")
    use_sample = st.checkbox("Use the built-in sample image instead", value=up is None)
    data = sample_image() if (use_sample or up is None) else up.getvalue()
    if len(data) > 200_000:
        st.error("File too large for the simulator. Please use one under 200 KB."); st.stop()

    if st.button("▶ Run full pipeline", type="primary"):
        t0 = time.perf_counter()
        oligos, meta = encode_file(data, scheme, parity)
        t_enc = time.perf_counter() - t0
        reads = sequence(oligos, cov, p_sub, p_ins, p_del, p_drop, rng=random.Random(seed))
        t0 = time.perf_counter()
        rec = recover(reads, meta)
        t_dec = time.perf_counter() - t0
        st.session_state.res = dict(data=data, oligos=oligos, meta=meta, reads=reads, rec=rec, t_enc=t_enc, t_dec=t_dec)

    R = st.session_state.get("res")
    if R is None or R["data"] != data:
        st.info("Press **Run full pipeline** to start.")
    else:
        oligos, meta, reads, rec = R["oligos"], R["meta"], R["reads"], R["rec"]
        st.markdown("### 1 · Your file")
        a, b = st.columns([1, 2])
        with a: show_file(data, f"{len(data):,} bytes")
        with b: st.write(f"SHA-256: `{sha(data)}`")

        st.markdown("### 2 · Encoded as DNA")
        q = quality(oligos); nb = sum(map(len, oligos))
        m = st.columns(5)
        for c, (t, v) in zip(m, [("Oligos", f"{len(oligos)}"), ("Total bases", f"{nb:,}"),
                                 ("Bits per base", f"{len(data) * 8 / nb:.2f}"), ("Longest repeat", f"{q['max_homopolymer']}"),
                                 ("GC content", f"{q['gc_min']:.0%}–{q['gc_max']:.0%}")]):
            c.markdown(f'<div class="card"><h4>{t}</h4><span class="n">{v}</span></div>', unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.image(barcode(oligos), caption=f"DNA barcode: first {min(60, len(oligos))} strands, one row per oligo")
        with c2:
            st.markdown("**First oligos** (index and checksum are inside each strand)")
            for o in oligos[:4]:
                st.markdown(f'<div class="seq">{colored(o)}</div>', unsafe_allow_html=True)
            st.caption(f"Encoding took {R['t_enc'] * 1000:.0f} ms. Last {meta['parity']} oligos of each 60-strand group are parity.")

        st.markdown("### 3 · Damage")
        got = sum(1 for i in reads)
        lost = len(oligos) - got
        st.write(f"{len(oligos) * cov:,} reads were simulated; **{lost}** strands were lost completely.")
        ex = next((i for i in reads), None)
        if ex is not None:
            st.markdown(f"Example: strand {ex}, original vs read #1 (red = changed)")
            st.markdown(f'<div class="seq">{colored(oligos[ex], 122)}</div>', unsafe_allow_html=True)
            st.markdown(diff_html(oligos[ex], reads[ex][0]), unsafe_allow_html=True)

        st.markdown("### 4 · Recovery and integrity check")
        if rec == data:
            st.markdown(f'<div class="ok"><b>✅ PASS</b>: recovered file is byte-for-byte identical.<br>'
                        f'Original: <code>{sha(data)[:32]}…</code><br>Recovered: <code>{sha(rec)[:32]}…</code></div>', unsafe_allow_html=True)
            x, y = st.columns(2)
            with x: show_file(data, "Original")
            with y: show_file(rec, "Recovered")
            st.download_button("⬇ Download recovered file", rec, file_name="recovered_file")
        else:
            st.markdown('<div class="bad"><b>❌ FAIL</b>: too much damage for the current redundancy. '
                        'Try more parity, more reads, or lower error rates in the sidebar.</div>', unsafe_allow_html=True)
        st.caption(f"Decoding took {R['t_dec']:.2f} s.")

# ------------------------------------------------------------------ experiments
with tab_exp:
    st.write("Sweep one error type and measure how often the file is recovered exactly. "
             "Compare **no error correction**, **CRC + Reed–Solomon (1 read)** and **full pipeline (consensus over your chosen reads)**.")
    kind = st.selectbox("Error type to sweep", ["p_sub", "p_drop", "p_del", "p_ins"],
                        format_func=lambda k: {"p_sub": "Substitutions", "p_drop": "Lost oligos", "p_del": "Deletions", "p_ins": "Insertions"}[k])
    rng_ = {"p_sub": [0.001, 0.01, 0.03, 0.06, 0.10], "p_drop": [0, 0.05, 0.10, 0.15, 0.20, 0.30],
            "p_del": [0.001, 0.005, 0.01, 0.02, 0.04], "p_ins": [0.001, 0.005, 0.01, 0.02, 0.04]}[kind]
    trials = st.slider("Trials per point", 3, 20, 5)
    if st.button("Run experiment"):
        small = (R["data"] if R else sample_image())[:3000]
        rows, bar = [], st.progress(0.0)
        for n, v in enumerate(rng_):
            res = {"No ECC (1 read)": 0, "CRC+RS (1 read)": 0, "Full pipeline": 0}
            for s in range(trials):
                kw = {kind: v}
                o0, m0 = encode_file(small, scheme, parity, use_ecc=False)
                r0 = sequence(o0, 1, rng=random.Random(s), **kw)
                res["No ECC (1 read)"] += recover_baseline(r0, m0) == small
                o1, m1 = encode_file(small, scheme, parity)
                r1 = sequence(o1, 1, rng=random.Random(s), **kw)
                res["CRC+RS (1 read)"] += recover(r1, m1, False) == small
                r2 = sequence(o1, cov, rng=random.Random(s), **kw)
                res["Full pipeline"] += recover(r2, m1) == small
            rows.append({"rate": str(v), **{k: x / trials * 100 for k, x in res.items()}})
            bar.progress((n + 1) / len(rng_))
        import pandas as pd
        df = pd.DataFrame(rows).set_index("rate")
        st.line_chart(df, y_label="Exact recovery (%)", x_label="Error rate")
        st.dataframe(df.round(0).astype(int).astype(str) + "%")
        st.caption(f"{trials} trials per point on a {len(small)}-byte file; results vary with trials and seed. Report your own measured numbers.")
