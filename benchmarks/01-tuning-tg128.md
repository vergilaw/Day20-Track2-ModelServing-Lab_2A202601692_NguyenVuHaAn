# 01 - Tune: thread-count sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Windows-AMD64` · llama.cpp `b10488`
CPU: **4 physical · 8 logical** cores · `ngl=99` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 38.0 | 56% |
| 2 | 37.5 | 55% |
| 4 | 67.9 | 100% |
| 8 | 38.9 | 57% |
| 16 | 42.6 | 63% |

**Best**: `-t 4` at 67.9 tok/s
**Slowest tested**: `-t 2` at 37.5 tok/s (1.81x spread)
**Against the physical-core default** (`-t 4`, 67.9 tok/s): 1.00x

Use this in your run:

```bash
LAB_N_THREADS=4 make bench
```

## Your explanation

Đỉnh hiệu năng (knee) nằm ở 4 luồng, tương đương số nhân vật lý. Tại đây băng thông bộ nhớ (memory bandwidth) đã được khai thác tối đa. Việc thêm luồng (từ 8 đến 16) khiến các luồng phải tranh giành tài nguyên bộ nhớ chung (contention) dẫn đến tụt hiệu năng.
