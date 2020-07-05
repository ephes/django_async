import time
import httpx
import concurrent.futures

from django.http import JsonResponse
from .viewfinder import get_all_functions


def api(request):
    time.sleep(1)
    payload = {"foo": "bar"}
    return JsonResponse(payload)


def threadpool_aggregation(request):
    num_iterations = 10
    sync_api_url = "http://localhost:8000/sync/api/"
    results = []
    urls = [sync_api_url for i in range(1, 1 + num_iterations)]
    s = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(httpx.get, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                r = future.result()
                results.append(r.json())
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))
    elapsed = time.perf_counter() - s
    print(f"fetch executed in {elapsed:0.2f} seconds.")
    result = {"responses": results}
    return JsonResponse(result)


all_functions = get_all_functions(globals().copy())