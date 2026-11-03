"""DNA Vault core: file -> DNA oligos -> noisy reads -> recovered file (software simulation)."""
import binascii, hashlib, math, random, struct, zlib
from collections import Counter
from reedsolo import RSCodec, ReedSolomonError

BASES = "ACGT"
PAYLOAD = 20          # bytes of file data per oligo
GROUP_N = 60          # oligos per RS group (data + parity)
OLIGO_BYTES = 2 + PAYLOAD + 2   # index + payload + crc16
TRITS = math.ceil(OLIGO_BYTES * 8 * math.log(2) / math.log(3))


# ---------- bytes <-> DNA ----------
def bytes_to_dna(b, scheme):
    if scheme == "naive":                       # 2 bits per base
        return "".join(BASES[(x >> s) & 3] for x in b for s in (6, 4, 2, 0))
    n = int.from_bytes(b, "big")                # "rotating": base-3, never repeats a base
    trits = []
    for _ in range(TRITS):
        n, t = divmod(n, 3)
        trits.append(t)
    prev, out = "A", []
    for t in reversed(trits):
        prev = [c for c in BASES if c != prev][t]
        out.append(prev)
    return "".join(out)


def dna_to_bytes(s, scheme):
    """Return bytes or None if the sequence is structurally invalid."""
    if scheme == "naive":
        if len(s) != OLIGO_BYTES * 4:
            return None
        v = [BASES.index(c) for c in s]
        return bytes((v[i] << 6) | (v[i+1] << 4) | (v[i+2] << 2) | v[i+3] for i in range(0, len(v), 4))
    if len(s) != TRITS:
        return None
    prev, n = "A", 0
    for c in s:
        opts = [x for x in BASES if x != prev]
        if c not in opts:
            return None
        n = n * 3 + opts.index(c)
        prev = c
    try:
        return n.to_bytes(OLIGO_BYTES, "big")
    except OverflowError:
        return None


def crc16(b):
    return binascii.crc_hqx(b, 0xFFFF)


# ---------- encoder ----------
def encode_file(data, scheme="rotating", parity=12, use_ecc=True):
    """Return (oligos: list[str], meta: dict)."""
    comp = zlib.compress(data, 9)
    blob = struct.pack(">I", len(comp)) + comp
    k = GROUP_N - parity if use_ecc else 1
    per_group_bytes = k * PAYLOAD
    n_groups = math.ceil(len(blob) / per_group_bytes)
    blob = blob.ljust(n_groups * per_group_bytes, b"\0")
    rows = []
    for g in range(n_groups):
        data_rows = [blob[(g*k+i)*PAYLOAD:(g*k+i+1)*PAYLOAD] for i in range(k)]
        if use_ecc:
            rs = RSCodec(parity)
            par = [bytearray(PAYLOAD) for _ in range(parity)]
            for j in range(PAYLOAD):
                cw = rs.encode(bytes(r[j] for r in data_rows))
                for p in range(parity):
                    par[p][j] = cw[k + p]
            data_rows += [bytes(p) for p in par]
        rows += data_rows
    oligos = []
    for idx, payload in enumerate(rows):
        body = struct.pack(">H", idx) + payload
        oligos.append(bytes_to_dna(body + struct.pack(">H", crc16(body)), scheme))
    meta = dict(scheme=scheme, parity=parity, use_ecc=use_ecc, n_groups=n_groups,
                n_oligos=len(oligos), k=k, orig_len=len(data))
    return oligos, meta


# ---------- channel ----------
def noisy_read(seq, p_sub, p_ins, p_del, rng):
    out = []
    for c in seq:
        if rng.random() < p_ins:
            out.append(rng.choice(BASES))
        r = rng.random()
        if r < p_del:
            continue
        if r < p_del + p_sub:
            out.append(rng.choice([b for b in BASES if b != c]))
        else:
            out.append(c)
    return "".join(out)


def sequence(oligos, coverage, p_sub=0, p_ins=0, p_del=0, p_drop=0, rng=None):
    """Return {oligo_id: [reads]} (cluster labels known: oracle clustering)."""
    rng = rng or random.Random()
    reads = {}
    for i, o in enumerate(oligos):
        if rng.random() < p_drop:
            continue
        reads[i] = [noisy_read(o, p_sub, p_ins, p_del, rng) for _ in range(coverage)]
    return reads


# ---------- decoder ----------
def _parse(seq, scheme):
    b = dna_to_bytes(seq, scheme)
    if b is None:
        return None
    body, crc = b[:-2], struct.unpack(">H", b[-2:])[0]
    if crc16(body) != crc:
        return None
    return struct.unpack(">H", body[:2])[0], body[2:]


def _consensus(reads):
    L = Counter(len(r) for r in reads).most_common(1)[0][0]
    same = [r for r in reads if len(r) == L]
    return "".join(Counter(col).most_common(1)[0][0] for col in zip(*same))


def recover(reads, meta, use_consensus=True):
    """Full decoder (CRC + consensus + RS erasure decoding). Returns bytes or None."""
    scheme, n_oligos, k = meta["scheme"], meta["n_oligos"], meta["k"]
    got = {}
    for cid, rs_ in reads.items():
        cands = ([_consensus(rs_)] if use_consensus else []) + list(rs_)
        for c in cands:
            p = _parse(c, scheme)
            if p and p[0] < n_oligos:
                got[p[0]] = p[1]
                break
    parity, n_groups = meta["parity"], meta["n_groups"]
    out = bytearray()
    for g in range(n_groups):
        base = g * GROUP_N if meta["use_ecc"] else g
        if not meta["use_ecc"]:
            out += got.get(base, bytes(PAYLOAD))
            continue
        erased = [i for i in range(GROUP_N) if base + i not in got]
        if len(erased) > parity:
            return None
        rows = [got.get(base + i, bytes(PAYLOAD)) for i in range(GROUP_N)]
        rs = RSCodec(parity)
        dec = [bytearray(PAYLOAD) for _ in range(k)]
        try:
            for j in range(PAYLOAD):
                col = bytearray(r[j] for r in rows)
                msg = rs.decode(col, erase_pos=erased)[0]
                for i in range(k):
                    dec[i][j] = msg[i]
        except ReedSolomonError:
            return None
        out += b"".join(bytes(r) for r in dec)
    return _unpack(bytes(out))


def recover_baseline(reads, meta):
    """No CRC, no consensus, no RS: trust the first read of each oligo."""
    scheme, out = meta["scheme"], bytearray()
    exp = OLIGO_BYTES * 4 if scheme == "naive" else TRITS
    for i in range(meta["n_oligos"]):
        r = reads.get(i, [None])[0]
        if r is None:
            out += bytes(PAYLOAD); continue
        r = (r + "A" * exp)[:exp]                      # force length
        if scheme == "rotating":                       # force validity
            fixed, prev = [], "A"
            for c in r:
                opts = [x for x in BASES if x != prev]
                c = c if c in opts else opts[0]
                fixed.append(c); prev = c
            r = "".join(fixed)
        b = dna_to_bytes(r, scheme)
        out += b[2:2+PAYLOAD] if b else bytes(PAYLOAD)
    return _unpack(bytes(out))


def _unpack(blob):
    try:
        n = struct.unpack(">I", blob[:4])[0]
        return zlib.decompress(blob[4:4+n])
    except Exception:
        return None


# ---------- sequence quality ----------
def quality(oligos):
    s = "".join(oligos)
    runs = max(len(m) for m in __import__("re").findall(r"A+|C+|G+|T+", s))
    gcs = [(o.count("G") + o.count("C")) / len(o) for o in oligos]
    return dict(max_homopolymer=runs, gc_mean=sum(gcs)/len(gcs), gc_min=min(gcs), gc_max=max(gcs))


def sha(b):
    return hashlib.sha256(b).hexdigest() if b is not None else None
