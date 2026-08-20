# 02 - Serve: load test + saturation reading

Host `Windows-AMD64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=4` ·
`ngl=99`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 141 | 2.41 | 3000 | 5000 | 5300 | 7.7 | 0.0% |
| 50 | 136 | 2.33 | 19000 | 21000 | 22000 | 39.6 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **0.96x** (19% of linear) |
| P95 latency | **4.20x** |
| Effective concurrency at 50 users | 39.6 vs `--parallel 4` slots (occupancy/slot ratio 9.90) |

**Saturated.** Throughput delivered only 0.96x for 5x the offered load, and effective concurrency (39.6) is at or above all 4 decode slots. Saturation sets in somewhere at or below 50 users; the load you added beyond that point became queue time rather than throughput.

Throughput moved 0.96x while P95 moved 4.20x. That gap is the goodput argument: past saturation you buy throughput by spending latency, and if your SLO is a P95 target then the requests you added are no longer being served within it. (This lab does not fix an SLO number for you -- pick one in your write-up and state how much goodput you keep at it.)

## My reading

Server bị bão hòa (saturate) ở ngay mức **dưới 10 users**. Bằng chứng là ở 10 users, mức độ concurrency hiệu dụng (Effective concurrency) đã đạt **7.7**, tức là cao hơn số lượng `--parallel 4` slots thực tế mà server đang có. Khi tăng tải lên 50 users, throughput không những không tăng mà còn giảm xuống 0.96x, trong khi độ trễ P95 phình to lên tới 4.20x. Điều này chứng tỏ toàn bộ lượng tải thêm vào chỉ nằm chờ trong hàng đợi (queue time) chứ không hề được xử lý.

Để tăng goodput (giữ P95 thấp dưới ngưỡng SLO ví dụ 5000ms), thông số đầu tiên tôi cần thay đổi là **tăng số lượng slots (`--parallel`)**, vì máy tôi còn dư rất nhiều RAM (15.7GB). Việc tăng slots sẽ cho phép server xử lý đồng thời nhiều request hơn thay vì bắt chúng phải chờ trong queue (đây là lý do trực tiếp khiến latency P95 tăng vọt).
