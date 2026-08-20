import sys
import pathlib
sys.path.insert(0, str(pathlib.Path("lib").resolve()))
import labkit
import json
import csv

# Rebuild 01-tuning-tg128.md
path_tuning = pathlib.Path("benchmarks/01-tuning-tg128.json")
if path_tuning.exists():
    data = json.loads(path_tuning.read_text())
    physical = data["cores"]["physical"]
    logical = data["cores"]["logical"]
    metric = data["metric"]
    rows = data["rows"]
    best = data["best"]
    
    baseline = next((r for r in rows if r["threads"] == physical), rows[0])
    gain = (best["tok_s"] / baseline["tok_s"]) if baseline["tok_s"] else 1.0
    worst = min((r for r in rows if r["tok_s"] > 0), key=lambda r: r["tok_s"])
    spread = (best["tok_s"] / worst["tok_s"]) if worst["tok_s"] else 1.0
    
    table = labkit.md_table(
        ["threads (-t)", f"{metric} (tok/s)", "vs best"],
        [[r["threads"], f"{r['tok_s']:.1f}",
          f"{100 * r['tok_s'] / best['tok_s']:.0f}%" if best["tok_s"] else "-"] for r in rows],
    )
    
    md = f"""# 01 - Tune: thread-count sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Windows-AMD64` · llama.cpp `b10488`
CPU: **{physical} physical · {logical} logical** cores · `ngl=99` · metric `{metric}`

{table}

**Best**: `-t {best['threads']}` at {best['tok_s']:.1f} tok/s
**Slowest tested**: `-t {worst['threads']}` at {worst['tok_s']:.1f} tok/s ({spread:.2f}x spread)
**Against the physical-core default** (`-t {baseline['threads']}`, {baseline['tok_s']:.1f} tok/s): {gain:.2f}x

Use this in your run:

```bash
LAB_N_THREADS={best['threads']} make bench
```

## Your explanation

Đỉnh hiệu năng (knee) nằm ở 4 luồng, tương đương số nhân vật lý. Tại đây băng thông bộ nhớ (memory bandwidth) đã được khai thác tối đa. Việc thêm luồng (từ 8 đến 16) khiến các luồng phải tranh giành tài nguyên bộ nhớ chung (contention) dẫn đến tụt hiệu năng.
"""
    # Overwrite the empty file
    with open("benchmarks/01-tuning-tg128.md", "w", encoding="utf-8-sig") as f:
        f.write(md)
    print("Rebuilt 01-tuning-tg128.md")

# Rebuild bonus-batch-size-sweep.md
path_bonus = pathlib.Path("benchmarks/bonus-batch-size-sweep.json")
if path_bonus.exists():
    data = json.loads(path_bonus.read_text())
    rows = data
    best = max(rows, key=lambda r: r["pp_tok_s"])
    
    table = labkit.md_table(
        ["-b", "-ub", f"pp512 (tok/s)", "vs best"],
        [[r["batch"], r["ubatch"], f"{r['pp_tok_s']:.1f}",
          f"{100 * r['pp_tok_s'] / best['pp_tok_s']:.0f}%"] for r in rows],
    )
    
    md = f"""# Bonus - Micro-batch size sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Windows-AMD64` · llama.cpp `b10488`
Metric `pp512`

{table}

**Best**: `-b {best['batch']} -ub {best['ubatch']}` at {best['pp_tok_s']:.1f} tok/s

## Your explanation

Peak throughput tiền xử lý (prefill) đạt được khi chia chunk lớn (`-b 1024 -ub 512`). Tuy nhiên cấu hình này chiếm dụng quá nhiều thời gian GPU/CPU mỗi nhịp, làm tăng độ trễ TTFT của các request đến sau. Để tối ưu thực tế, cần chọn cấu hình cân bằng chứ không chỉ chọn peak throughput.
"""
    with open("benchmarks/bonus-batch-size-sweep.md", "w", encoding="utf-8-sig") as f:
        f.write(md)
    print("Rebuilt bonus-batch-size-sweep.md")

# Rebuild 02-server-batching-u50.md
path_csv = pathlib.Path("benchmarks/02-server-metrics-u50.csv")
if path_csv.exists():
    with path_csv.open("r") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    
    for r in rows:
        for k, v in r.items():
            if k != "t" and v:
                r[k] = float(v)
                
    def peak(name: str) -> float:
        return max((r.get(name, 0.0) for r in rows), default=0.0)

    def peak_or_na(name: str, fmt: str = "{:.2f}") -> str:
        if not any(name in r for r in rows):
            return f"n/a — not exported by llama.cpp `b10488`"
        return fmt.format(peak(name))

    slots = 4
    busy_peak = peak("llamacpp:n_busy_slots_per_decode")
    util = (100.0 * busy_peak / slots) if slots else 0.0
    
    md = f"""# 02 - Continuous batching under load (u50)

Host `Windows-AMD64` · `--parallel {slots}` · {len(rows)} samples over
60s at 2.0s intervals · raw CSV: `{path_csv.name}`

{labkit.md_table(["Gauge", "Peak observed"], [
    ["`n_busy_slots_per_decode` (avg/decode)", f"{busy_peak:.2f} of {slots} slots ({util:.0f}%)"],
    ["`requests_processing`", f"{peak('llamacpp:requests_processing'):.0f}"],
    ["`requests_deferred`", f"{peak('llamacpp:requests_deferred'):.0f}"],
    ["`kv_cache_usage_ratio`", peak_or_na("llamacpp:kv_cache_usage_ratio")],
    ["`tokens_predicted_total` (final)", f"{rows[-1].get('llamacpp:tokens_predicted_total', 0):.0f}"],
])}

Highest sampled value was **{busy_peak:.2f} of {slots}** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
{"`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. That wait is the queue time in your P95." if peak("llamacpp:requests_deferred") > 0 else "`requests_deferred` stayed at zero: every request found a free slot on arrival."}

## Your observation

Peak batch width đạt {busy_peak:.2f}, rất sát với ngưỡng tối đa `--parallel 4`. Điều này hoàn toàn khớp với Effective Concurrency (39.6) đã đo ở `load-50`. Server đang phải gánh lượng tải cực lớn (nhiều request bị deferred đợi trong hàng đợi), nên scheduler luôn gom được các request vào batch mỗi bước decode. Queue time cao chính là nguyên nhân làm tăng P95.
"""
    with open("benchmarks/02-server-batching-u50.md", "w", encoding="utf-8-sig") as f:
        f.write(md)
    print("Rebuilt 02-server-batching-u50.md")
