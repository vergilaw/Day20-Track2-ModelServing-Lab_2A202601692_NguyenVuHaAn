# Bonus - Micro-batch size sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Windows-AMD64` · llama.cpp `b10488`
Metric `pp512`

| -b | -ub | pp512 (tok/s) | vs best |
|:--|--:|--:|--:|
| 128 | 128 | 2454.4 | 85% |
| 256 | 256 | 2778.0 | 96% |
| 512 | 256 | 2812.5 | 97% |
| 512 | 512 | 2806.2 | 97% |
| 1024 | 512 | 2897.7 | 100% |
| 2048 | 512 | 2840.6 | 98% |

**Best**: `-b 1024 -ub 512` at 2897.7 tok/s

## Your explanation

Peak throughput tiền xử lý (prefill) đạt được khi chia chunk lớn (`-b 1024 -ub 512`). Tuy nhiên cấu hình này chiếm dụng quá nhiều thời gian GPU/CPU mỗi nhịp, làm tăng độ trễ TTFT của các request đến sau. Để tối ưu thực tế, cần chọn cấu hình cân bằng chứ không chỉ chọn peak throughput.
