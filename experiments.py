import os, random, time, json
from dnavault import *

TRIALS = 10
rng_data = random.Random(0)
TEXT = open(__file__, "rb").read() * 4 + open(os.path.join(os.path.dirname(__file__), "dnavault.py"), "rb").read()
RANDOM = bytes(rng_data.getrandbits(8) for _ in range(4096))   # incompressible, like JPEG/PNG data

CONFIGS = {
    "A: no ECC, 1 read":            dict(use_ecc=False, cov=1, mode="baseline"),
    "B: CRC+RS, 1 read":            dict(use_ecc=True,  cov=1, mode="ecc", cons=False),
    "C: CRC+RS+consensus, 10 reads": dict(use_ecc=True, cov=10, mode="ecc", cons=True),
}


def trial(data, cfg, scheme, seed, **noise):
    rng = random.Random(seed)
    oligos, meta = encode_file(data, scheme, use_ecc=cfg["use_ecc"])
    reads = sequence(oligos, cfg["cov"], rng=rng, **noise)
    rec = recover_baseline(reads, meta) if cfg["mode"] == "baseline" else recover(reads, meta, cfg["cons"])
    return rec == data


def rate(data, cfg, scheme, **noise):
    return sum(trial(data, cfg, scheme, s, **noise) for s in range(TRIALS)) / TRIALS


def sweep(title, key, values, scheme="rotating", data=TEXT):
    print(f"\n### {title}  (scheme={scheme}, {TRIALS} trials/cell, exact-hash success)")
    print("| " + key + " | " + " | ".join(CONFIGS) + " |")
    print("|---|" + "---|" * len(CONFIGS))
    for v in values:
        row = [f"{rate(data, c, scheme, **{key: v}):.0%}" for c in CONFIGS.values()]
        print(f"| {v} | " + " | ".join(row) + " |")


if __name__ == "__main__":
    print(f"Test files: text={len(TEXT)} B, random={len(RANDOM)} B; oligo={OLIGO_BYTES*4} nt (naive) / {TRITS} nt (rotating)")

    print("\n### Sequence quality (A: naive vs rotating, incl. random data)")
    for name, d in (("text", TEXT), ("random", RANDOM)):
        for sch in ("naive", "rotating"):
            o, m = encode_file(d, sch)
            print(name, sch, quality(o))

    print("\n### Zero errors, scheme x file")
    for name, d in (("text", TEXT), ("random", RANDOM)):
        for sch in ("naive", "rotating"):
            print(name, sch, "recovered:", trial(d, CONFIGS["C: CRC+RS+consensus, 10 reads"], sch, 0))

    sweep("Substitution errors", "p_sub", [0.001, 0.01, 0.03, 0.06, 0.10])
    sweep("Whole-oligo dropout (missing fragments)", "p_drop", [0.0, 0.05, 0.10, 0.15, 0.20, 0.30])
    sweep("Deletion errors", "p_del", [0.001, 0.005, 0.01, 0.02, 0.04])
    sweep("Insertion errors", "p_ins", [0.001, 0.005, 0.01, 0.02, 0.04])
    sweep("Substitution, naive scheme", "p_sub", [0.01, 0.03, 0.06], scheme="naive")

    print("\n### File size vs bases / overhead / time (rotating, parity=12, ECC on)")
    print("| file | input B | compressed B | oligos | total bases | bits/base (input) | encode time |")
    print("|---|---|---|---|---|---|---|")
    for name, d in (("text x1", TEXT[:len(TEXT)//4]), ("text x4", TEXT), ("random 4KB", RANDOM), ("random 16KB", bytes(rng_data.getrandbits(8) for _ in range(16384)))):
        t = time.perf_counter(); o, m = encode_file(d, "rotating"); dt = time.perf_counter() - t
        bases = sum(map(len, o))
        print(f"| {name} | {len(d)} | {len(zlib.compress(d,9))} | {len(o)} | {bases} | {len(d)*8/bases:.3f} | {dt*1000:.0f} ms |")
    for sch in ("naive", "rotating"):
        o, m = encode_file(RANDOM, sch)
        print(f"random 4KB {sch}: bits/base = {len(RANDOM)*8/sum(map(len,o)):.3f}")
