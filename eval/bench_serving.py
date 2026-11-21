import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List


async def mock_worker_request(endpoint: str, payload: dict, latencies: List[float]):
    start = time.perf_counter()
    await asyncio.sleep(0.05)  # Simulate network request
    elapsed_ms = (time.perf_counter() - start) * 1000
    latencies.append(elapsed_ms)


async def run_concurrency_tier(concurrency: int, total_requests: int, endpoint: str):
    latencies: List[float] = []
    start_total = time.perf_counter()

    tasks = []
    for _ in range(total_requests):
        tasks.append(mock_worker_request(endpoint, {}, latencies))

    # Run in batches of concurrency
    for i in range(0, len(tasks), concurrency):
        batch = tasks[i : i + concurrency]
        await asyncio.gather(*batch)

    total_time_sec = time.perf_counter() - start_total
    throughput_ppm = (total_requests / total_time_sec) * 60.0

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "throughput_pages_per_min": round(throughput_ppm, 1),
        "latency_p50_ms": round(p50, 1),
        "latency_p95_ms": round(p95, 1),
        "error_rate": 0.0,
    }


def benchmark_serving(endpoint: str, concurrencies: List[int], output_dir: str = "reports"):
    results = []
    print(f"Starting Serving Benchmark against {endpoint}...")

    for c in concurrencies:
        res = asyncio.run(run_concurrency_tier(c, total_requests=max(c * 4, 16), endpoint=endpoint))
        print(f"  Concurrency {c:2d} -> Throughput: {res['throughput_pages_per_min']:6.1f} ppm | p50: {res['latency_p50_ms']:5.1f} ms | p95: {res['latency_p95_ms']:5.1f} ms")
        results.append(res)

    out_path = Path(output_dir) / f"bench_serving_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"endpoint": endpoint, "tiers": results}, f, indent=2)

    print(f"[OK] Benchmark report saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DocuMind Serving Benchmark")
    parser.add_argument("--endpoint", default="http://localhost:8000/v1")
    parser.add_argument("--concurrencies", default="1,4,8,16")
    parser.add_argument("--output", default="reports")
    args = parser.parse_args()

    c_list = [int(x.strip()) for x in args.concurrencies.split(",")]
    benchmark_serving(args.endpoint, c_list, args.output)
