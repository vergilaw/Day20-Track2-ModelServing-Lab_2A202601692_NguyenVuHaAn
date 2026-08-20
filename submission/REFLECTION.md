# Reflection — Day 20 Lab (Personal Report)

> **Đây là báo cáo cá nhân.** Số liệu của bạn **không** so sánh được với bạn cùng lớp
> — chỉ so **before vs after trên chính máy bạn**. Rubric chấm độ rõ ràng của setup,
> đo lường và **lập luận**, không chấm tốc độ tuyệt đối.
>
> `make verify` sẽ fail nếu còn placeholder chưa điền. Đó là cố ý.

**Họ Tên:** Nguyen Vu Ha An
**Cohort:** A20-K1
**Ngày submit:** 2026-08-20

---

## 1. Hardware & runtime  *(rubric 1, 2 — 10 điểm)*

> Từ `make probe`. Paste output hoặc điền tay.

- **OS:** Windows 11
- **CPU:** 11th Gen Intel(R) Core(TM) i5-11300H @ 3.10GHz
- **Cores:** 4 physical / 8 logical
- **CPU extensions:** AVX2
- **RAM:** 15.7 GB
- **Accelerator:** nvidia_cuda, vulkan
- **llama.cpp asset đã tải:** llama-b10488-bin-win-cuda-12.4-x64.zip
- **Model đã dùng:** Gemma 4 E2B (`LAB_MODEL=`gemma4-e2b)
- **Quantization:** gemma-4-E2B-it-UD-Q4_K_XL.gguf + gemma-4-E2B-it-UD-Q2_K_XL.gguf

**Chạy ở đâu:** laptop của tôi
*(Nếu dùng cloud fallback: nói rõ vì sao — RAM < 8 GB, setup fail, v.v. Không mất điểm.)*

**Setup story** (≤ 80 chữ): điều gì cần thay đổi để lab chạy trên máy bạn? Có bước
nào fail rồi phải workaround không?

Cần thêm `$env:PYTHONIOENCODING='utf-8'` khi chạy các script vì PowerShell trên Windows 11 mặc định dùng mã hóa cp1258 gây lỗi in ký tự đặc biệt (emoji, box-drawing). Ngoài ra script Python `serve.py` được chỉnh sửa dùng `subprocess.run` thay vì `os.execv` để tránh bị đứng màn hình trên Windows.

---

## 2. Đo lường  *(rubric 3, 4, 5 — 20 điểm)*

> Paste bảng từ `benchmarks/01-quickstart-results.md` (`make bench` tự sinh).

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|---|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 4018 | 250 / 393 | 13.9 / 15.7 | 1105 / 1247 / 1247 | 72.1 |
| UD-Q2_K_XL | 2.24 | 4531 | 250 / 524 | 14.0 / 15.0 | 1107 / 1366 / 1366 | 71.5 |

**Quan sát** (≤ 60 chữ): 2-bit nhanh hơn bao nhiêu, và **có đáng không**? Bạn đã thử
hỏi cùng một câu trên cả hai (`make serve` vs `.venv/bin/python labs/02-serve/serve.py --compare`)
chưa? Chất lượng khác nhau thế nào?

Bản 2-bit chỉ tiết kiệm 0.73GB nhưng giảm chất lượng câu trả lời rõ rệt, trong khi tốc độ decode (71.5 tok/s so với 72.1 tok/s) gần như không khác biệt do băng thông bộ nhớ đủ đáp ứng cả hai. Bản 4-bit đáng dùng hơn nhiều.

---

## 3. Serving under load  *(rubric 8, 9, 10 — 20 điểm)*

> Từ `benchmarks/02-server-results.md` (`make load-report`).

| Users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|--:|--:|--:|--:|--:|--:|--:|
| 10 | 2.41 | 3000 | 5000 | 5300 | 7.7 | 0.0% |
| 50 | 2.33 | 19000 | 21000 | 22000 | 39.6 | 0.0% |

- **Offered load tăng 5×, throughput thực tăng:** 0.96×
- **P95 tăng:** 4.20×
- **Effective concurrency ở 50 users:** 39.6 so với `--parallel` = 4 slots

**Peak `llamacpp:n_busy_slots_per_decode`** (từ `make metrics` khi `make load-50` đang
chạy): 3.94 / 4 slots

**Saturation reading** (≤ 80 chữ): server của bạn bão hoà ở đâu, và **bằng chứng nào**
thuyết phục bạn? Nếu P95 tăng nhanh hơn RPS thì phần latency thêm đó là queue time hay
compute time — bạn biết bằng cách nào? Nếu bạn phải nâng goodput@SLO, bạn sẽ đổi knob
nào **trước**, và vì sao knob đó?

Server bão hòa ở mức dưới 10 users vì concurrency hiệu dụng (7.7) vượt quá `--parallel=4` slots. P95 tăng vọt 4.2x chứng tỏ phần lớn thời gian là queue time. Để tăng goodput, knob đầu tiên cần chỉnh là nâng `--parallel` vì RAM (15.7GB) vẫn còn dư rất nhiều.

---

## 4. Integration  *(rubric 12, 13 — 15 điểm)*

> Từ `make pipeline`. Nói thật cái nào real, cái nào stub — stub **không** mất điểm.

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | pipeline.py | real |
| N17 Data pipeline | Embeddings | stubbed |
| N18 Lakehouse | Vector DB | stubbed |
| N19 Vector + features | - | stubbed |
| N20 Serving | `llama-server` | real |

**Latency split** (mean của 3 query, từ output của `pipeline.py`):

- embed: 0.0ms
- retrieve: 0.3ms
- llm: 2917.0ms
- **stage chiếm nhiều nhất:** llm (100% của total)

**Reflection** (≤ 60 chữ): bottleneck ở đâu? Có khớp với kỳ vọng của bạn không? Nếu
phải giảm latency của pipeline này 2×, bạn sẽ tấn công vào đâu?

Bottleneck hoàn toàn nằm ở khâu LLM, đúng như kỳ vọng vì text generation rất nặng. Để giảm nửa latency, tôi sẽ tối ưu N19 bằng Semantic Cache hoặc dùng model nhỏ hơn/lượng context nhỏ hơn để tăng tốc LLM.

---

## 5. The single change that mattered most  *(rubric 11 — 10 điểm)*

> **Phần quan trọng nhất của report.** Không cần bonus track: `make tune` đã cho bạn
> một before/after thật (`benchmarks/01-tuning-tg128.md`). Đổi quantization,
> `LAB_N_CTX`, hay `--parallel` rồi đo lại cũng được.

**Change:** hạ -t (threads) từ 8 xuống 4

```
before:  38.9 tok/s
after:   67.9 tok/s
speedup: 1.74×
```

**Tại sao nó work** (1–2 đoạn — đây là phần grader đọc kỹ nhất):

Trên máy có 4 nhân vật lý (8 luồng ảo), việc chạy ở 1 luồng sẽ bị thắt cổ chai ở năng lực tính toán của CPU (compute-bound). Khi nâng lên đúng 4 luồng bằng với số nhân vật lý, tốc độ tăng 1.74× (lên 67.9 tok/s) và chạm ngưỡng thắt cổ chai băng thông bộ nhớ (memory-bandwidth bound). Tại điểm này, các nhân vật lý đã vắt kiệt tối đa lượng RAM có thể đọc mỗi giây.

Tuy nhiên, việc tăng tiếp vượt quá số nhân vật lý (như nhồi 8 luồng) khiến các luồng ảo (Hyper-threading) phải tranh giành chung một băng thông bộ nhớ. Nó sinh ra chi phí điều phối (context switching overhead) và tranh chấp cache (cache thrashing), khiến các luồng giẫm chân lên nhau và hiệu năng sụt giảm ngược lại (xuống 38.9 tok/s). Điều này chứng minh quá trình giải mã (decode) bị giới hạn bởi memory bandwidth chứ không phải CPU, và việc nhồi quá nhiều thread sẽ phản tác dụng.

---

## 6. Bonus  *(optional — tối đa 20 điểm)*

> Bỏ trống nếu không làm. Xem `bonus/README.md`. Đừng làm hết — **một** finding sâu
> ăn điểm hơn năm bảng nông.

**Đã làm:** B2 sweep-batch và B5 semantic-cache-offline

**Numbers:**

```
before:  2454.4 tok/s
after:   2897.7 tok/s
speedup: 1.18×
```

**Điều này nói lên gì mà deck chưa nói:**

Phần đo `sweep-batch` chỉ cho thấy một mặt của bức tranh là throughput tiền xử lý (prefill) cao nhất (với -b 1024 -ub 512 đạt 2897 tok/s). Tuy nhiên, đánh đổi lại là độ trễ TTFT của các request xếp hàng phía sau sẽ tăng cao vì micro-batch lớn chiếm dụng thiết bị (hogging) lâu hơn trong từng nhịp tính toán. Để vận hành thực tế ở môi trường tải cao, cần đo thêm P95 qua bài test load để chọn cấu hình cân bằng, chứ không chỉ chọn peak throughput. (Với B5 offline semantic-cache, Hit rate đạt 3/8 tiết kiệm 100% LLM).

---

## 7. Điều làm bạn ngạc nhiên nhất  *(optional)*

_(1–2 câu. Không bắt buộc, nhưng grader đọc hết.)_

Việc máy có 8 luồng nhưng chỉ chạy tốt nhất với 4 luồng làm tôi khá ngạc nhiên, nó trực quan hóa rõ ràng khái niệm memory-bandwidth bound.

---

## 8. Self-check trước khi push

- [ ] `hardware.json` committed
- [ ] `models/active.json` committed
- [ ] `benchmarks/01-quickstart-results.md` committed (`make bench`)
- [ ] `benchmarks/01-tuning-tg128.md` committed (`make tune`)
- [ ] `benchmarks/02-server-results.md` committed (`make load-report`)
- [ ] `benchmarks/02-server-batching-u50.md` hoặc `-metrics-u50.csv` committed (`make metrics`)
- [ ] `benchmarks/locust-10_stats.csv` + `locust-50_stats.csv` committed (`make load-10` / `load-50`)
- [ ] `benchmarks/03-integration-results.md` committed (`make pipeline`)
- [ ] Mọi section **"required — replace this line"** trong các file `benchmarks/*.md`
      đã được thay bằng nhận xét của bạn
- [ ] 5 screenshots trong `submission/screenshots/`
- [ ] `make verify` → **exit 0**
- [ ] Repo GitHub ở chế độ **public**
- [ ] Đã paste public URL vào VinUni LMS
- [ ] **Không** commit `models/*.gguf` hay `runtime/` (đã có trong `.gitignore`)

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Private → grader không
xem được → 0 điểm.
