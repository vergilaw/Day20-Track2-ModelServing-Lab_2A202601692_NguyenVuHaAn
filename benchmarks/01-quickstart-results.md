# 01 - Measure: latency baseline

Model `Gemma 4 E2B` · host `Windows-AMD64` · llama.cpp `b10488`
Settings: `threads=4` `ngl=99` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `UD-Q4_K_XL` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 4018 | 250 / 393 | 13.9 / 15.7 | 1105 / 1247 / 1247 | 72.1 |
| UD-Q2_K_XL | 2.24 | 4531 | 250 / 524 | 14.0 / 15.0 | 1107 / 1366 / 1366 | 71.5 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` and `UD-Q4_K_XL` decode within 2% of each other here, for 0.73 GB difference on disk.

## My observation

Bản 2-bit (UD-Q2_K_XL) nhỏ hơn bản 4-bit (UD-Q4_K_XL) khoảng 0.73 GB (~25% dung lượng). Tuy nhiên, về mặt tốc độ, số token xử lý mỗi giây (Decode tok/s) của hai bản hầu như không khác biệt (71.5 tok/s so với 72.1 tok/s). Vì máy có 15.7 GB RAM khá rộng rãi cho cả 2 model, việc đánh đổi chất lượng câu trả lời lấy 0.73 GB RAM là không đáng. Qua kiểm tra thực tế, bản 2-bit thường đưa ra câu trả lời ngớ ngẩn hơn so với bản 4-bit. Do đó, **bản 4-bit (Q4)** là sự lựa chọn tốt nhất.
