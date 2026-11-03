Test files: text=20545 B, random=4096 B; oligo=96 nt (naive) / 122 nt (rotating)

### Sequence quality (A: naive vs rotating, incl. random data)
text naive {'max_homopolymer': 52, 'gc_mean': 0.47708333333333336, 'gc_min': 0.1875, 'gc_max': 0.6666666666666666}
text rotating {'max_homopolymer': 2, 'gc_mean': 0.49818989071038255, 'gc_min': 0.4016393442622951, 'gc_max': 0.5901639344262295}
random naive {'max_homopolymer': 84, 'gc_mean': 0.4347222222222222, 'gc_min': 0.041666666666666664, 'gc_max': 0.625}
random rotating {'max_homopolymer': 2, 'gc_mean': 0.5017759562841531, 'gc_min': 0.4098360655737705, 'gc_max': 0.5901639344262295}

### Zero errors, scheme x file
text naive recovered: True
text rotating recovered: True
random naive recovered: True
random rotating recovered: True

### Substitution errors  (scheme=rotating, 10 trials/cell, exact-hash success)
| p_sub | A: no ECC, 1 read | B: CRC+RS, 1 read | C: CRC+RS+consensus, 10 reads |
|---|---|---|---|
| 0.001 | 0% | 80% | 100% |
| 0.01 | 0% | 0% | 100% |
| 0.03 | 0% | 0% | 100% |
| 0.06 | 0% | 0% | 100% |
| 0.1 | 0% | 0% | 100% |

### Whole-oligo dropout (missing fragments)  (scheme=rotating, 10 trials/cell, exact-hash success)
| p_drop | A: no ECC, 1 read | B: CRC+RS, 1 read | C: CRC+RS+consensus, 10 reads |
|---|---|---|---|
| 0.0 | 100% | 100% | 100% |
| 0.05 | 0% | 100% | 100% |
| 0.1 | 0% | 100% | 80% |
| 0.15 | 0% | 70% | 30% |
| 0.2 | 0% | 30% | 0% |
| 0.3 | 0% | 0% | 0% |

### Deletion errors  (scheme=rotating, 10 trials/cell, exact-hash success)
| p_del | A: no ECC, 1 read | B: CRC+RS, 1 read | C: CRC+RS+consensus, 10 reads |
|---|---|---|---|
| 0.001 | 0% | 80% | 100% |
| 0.005 | 0% | 0% | 100% |
| 0.01 | 0% | 0% | 100% |
| 0.02 | 0% | 0% | 0% |
| 0.04 | 0% | 0% | 0% |

### Insertion errors  (scheme=rotating, 10 trials/cell, exact-hash success)
| p_ins | A: no ECC, 1 read | B: CRC+RS, 1 read | C: CRC+RS+consensus, 10 reads |
|---|---|---|---|
| 0.001 | 0% | 90% | 100% |
| 0.005 | 0% | 0% | 100% |
| 0.01 | 0% | 0% | 100% |
| 0.02 | 0% | 0% | 0% |
| 0.04 | 0% | 0% | 0% |

### Substitution, naive scheme  (scheme=naive, 10 trials/cell, exact-hash success)
| p_sub | A: no ECC, 1 read | B: CRC+RS, 1 read | C: CRC+RS+consensus, 10 reads |
|---|---|---|---|
| 0.01 | 0% | 0% | 100% |
| 0.03 | 0% | 0% | 100% |
| 0.06 | 0% | 0% | 100% |

### File size vs bases / overhead / time (rotating, parity=12, ECC on)
| file | input B | compressed B | oligos | total bases | bits/base (input) | encode time |
|---|---|---|---|---|---|---|
| text x1 | 5136 | 1369 | 120 | 14640 | 2.807 | 5 ms |
| text x4 | 20545 | 3823 | 240 | 29280 | 5.613 | 10 ms |
| random 4KB | 4096 | 4107 | 300 | 36600 | 0.895 | 12 ms |
| random 16KB | 16384 | 16395 | 1080 | 131760 | 0.995 | 43 ms |
random 4KB naive: bits/base = 1.138
random 4KB rotating: bits/base = 0.895
