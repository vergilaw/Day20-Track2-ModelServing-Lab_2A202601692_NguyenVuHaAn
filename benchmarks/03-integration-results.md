# 03 - Integrate: RAG pipeline run

Host `Windows-AMD64` · llama.cpp `b10488` ·
retrieval backend: **keyword overlap** · 3 queries

| Query | Contexts retrieved | embed (ms) | retrieve (ms) | llm (ms) | total (ms) |
|:--|--:|--:|--:|--:|--:|
| Why is goodput more useful than raw throughp... | goodput, paged, radix | 0.0 | 0.9 | 3110.8 | 3111.7 |
| What problem does PagedAttention actually so... | paged, radix, disagg | 0.0 | 0.1 | 2820.8 | 2820.9 |
| When does splitting prefill and decode help?... | disagg, radix, batching | 0.0 | 0.0 | 2819.5 | 2819.6 |

Mean per stage (ms): embed **0.0** · retrieve **0.3** ·
llm **2917.0** · total **2917.4**
Dominant stage: **llm** (100% of total)

## Answers returned

**Why is goodput more useful than raw throughput?**

> Goodput@SLO counts only the requests per second that met the TTFT and TPOT targets. Throughput at saturation ignores SLOs.

**What problem does PagedAttention actually solve?**

> PagedAttention stores the KV cache in non-contiguous pages, removing the internal fragmentation that wasted most GPU memory.

**When does splitting prefill and decode help?**

> Splitting prefill and decode helps because prefill is compute-bound and decode is memory-bandwidth-bound.


## My reading

- **N16 (Gateway/Pipeline):** Real (script `pipeline.py` đóng vai trò điều phối).
- **N17 (Embeddings):** Stubbed (đang dùng fallback là keyword overlap, thời gian embed = 0.0ms).
- **N18 (Vector DB / Retrieval):** Stubbed (tìm kiếm trực tiếp bằng keyword, không dùng vector db thực sự).
- **N19 (LLM):** Real (gọi đến `llama-server` thực sự trên port 8080).

**Giai đoạn chiếm nhiều thời gian nhất (Dominant stage):** LLM (chiếm gần như 100% thời gian - 2917ms). Điều này hoàn toàn đúng dự đoán vì quá trình sinh text (decode) của LLM tốn rất nhiều tài nguyên tính toán và bị thắt cổ chai bởi băng thông bộ nhớ (memory bandwidth).

**Nếu muốn giảm một nửa độ trễ:** Tôi sẽ tập trung tối ưu hóa **N19 (LLM)** bằng các biện pháp như: sử dụng mô hình nhỏ hơn, bật tính năng Semantic Caching (để trả lời nhanh nếu trùng câu hỏi cũ), hoặc sử dụng phần cứng chuyên dụng (chạy GPU thay vì CPU) vì đây là thành phần tiêu tốn thời gian lớn nhất.
