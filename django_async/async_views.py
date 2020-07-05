import time
import httpx
import asyncio

from django.http import JsonResponse
from .viewfinder import get_all_functions


async def api(requst):
    await asyncio.sleep(1)
    payload = {"foo": "bar"}
    return JsonResponse(payload)


async def aggregation_of_sync_view(request):
    # start server like this:
    # uvicorn --workers 10 django_async.asgi:application
    print("locals: ", locals())
    responses = []
    url = "http://127.0.0.1:8000/sync/api/"
    urls = [url for _ in range(10)]
    s = time.perf_counter()
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[client.get(url) for url in urls])
        responses = [r.json() for r in responses]
    elapsed = time.perf_counter() - s
    print(f"fetch executed in {elapsed:0.2f} seconds.")
    result = {"responses": responses}
    return JsonResponse(result)


async def aggregation_of_async_view(request):
    # start server like this:
    # uvicorn django_async.asgi:application
    print("locals: ", locals())
    responses = []
    url = "http://127.0.0.1:8000/async/api/"
    urls = [url for _ in range(10)]
    s = time.perf_counter()
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[client.get(url) for url in urls])
        responses = [r.json() for r in responses]
    elapsed = time.perf_counter() - s
    print(f"fetch executed in {elapsed:0.2f} seconds.")
    result = {"responses": responses}
    return JsonResponse(result)


all_functions = get_all_functions(globals().copy())