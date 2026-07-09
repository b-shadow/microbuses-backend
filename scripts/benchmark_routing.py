from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROUTING_URL = "http://127.0.0.1:8000/api/v1/routing/calculate"
WALKING_URL = "http://127.0.0.1:8000/api/v1/walking-network/route"

ROUTING_BODY = {
    "origin": {"lat": -17.7833, "lng": -63.1821},
    "destination": {"lat": -17.7900, "lng": -63.1750},
    "max_transfers": 3,
    "boarding_mode": "ANYWHERE_ON_ROUTE",
}

WALKING_BODY = {
    "origin_lat": -17.7833,
    "origin_lng": -63.1821,
    "destination_lat": -17.7900,
    "destination_lng": -63.1750,
}


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((percent / 100) * (len(ordered) - 1)))
    return ordered[index]


def post_json(url: str, body: dict, timeout: float) -> tuple[int, float, str]:
    payload = json.dumps(body).encode("utf-8")
    request = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read()
            status = response.status
            error = ""
    except HTTPError as exc:
        status = exc.code
        error = exc.reason
    except URLError as exc:
        status = 0
        error = str(exc.reason)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return status, elapsed_ms, error


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark simple del endpoint de calculo de rutas.")
    parser.add_argument("--preset", choices=["routing", "walking"], default="routing")
    parser.add_argument("--url", help="URL completa del endpoint. Si se omite, se usa segun --preset.")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--body-json", help="JSON del body. Si se omite usa coordenadas demo de Santa Cruz.")
    args = parser.parse_args()

    default_url = WALKING_URL if args.preset == "walking" else ROUTING_URL
    default_body = WALKING_BODY if args.preset == "walking" else ROUTING_BODY
    url = args.url or default_url
    body = json.loads(args.body_json) if args.body_json else default_body
    started = time.perf_counter()
    results: list[tuple[int, float, str]] = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(post_json, url, body, args.timeout) for _ in range(args.requests)]
        for future in as_completed(futures):
            results.append(future.result())

    total_seconds = time.perf_counter() - started
    times = [elapsed for _, elapsed, _ in results]
    ok_count = sum(1 for status, _, _ in results if 200 <= status < 300)
    by_status: dict[int, int] = {}
    for status, _, _ in results:
        by_status[status] = by_status.get(status, 0) + 1

    print(f"url={url}")
    print(f"requests={args.requests} concurrency={args.concurrency} ok={ok_count}")
    print(f"status_counts={dict(sorted(by_status.items()))}")
    print(f"total_seconds={total_seconds:.2f} rps={args.requests / total_seconds:.2f}")
    print(f"min_ms={min(times):.2f} avg_ms={statistics.mean(times):.2f} p50_ms={percentile(times, 50):.2f}")
    print(f"p95_ms={percentile(times, 95):.2f} max_ms={max(times):.2f}")

    errors = [error for _, _, error in results if error]
    if errors:
        print(f"sample_error={errors[0]}")


if __name__ == "__main__":
    main()
