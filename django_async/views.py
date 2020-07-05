import time
import types
import httpx
import asyncio

from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async

from django.http import HttpResponse
from django.http import JsonResponse

from .viewfinder import get_all_functions


def sync_hello_world_view(request):
    html = "<html><body>Hello World!</body></html>"
    return HttpResponse(html)


async def async_hello_world_view(request):
    html = "<html><body>Hello Async World!</body></html>"
    return HttpResponse(html)


def sync_api_view(request):
    time.sleep(1)
    payload = {"foo": "bar"}
    return JsonResponse(payload)


async def async_api_view(requst):
    payload = {"foo": "bar"}
    return JsonResponse(payload)


def sync_aggregation_view(request):
    # this works only in multithreading mode
    responses = []
    for num in range(5):
        r = httpx.get("http://127.0.0.1:8001/sync_api_view/")
        responses.append(r.json())
    result = {"responses": responses}
    return JsonResponse(result)


async def async_aggregation_from_sync_view(request):
    # ok, but this is working
    # start server like this:
    # uvicorn --workers 10 django_async.asgi:application
    print("locals: ", locals())
    responses = []
    url = "http://127.0.0.1:8000/sync_api_view/"
    urls = [url for _ in range(10)]
    s = time.perf_counter()
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[client.get(url) for url in urls])
        responses = [r.json() for r in responses]
    elapsed = time.perf_counter() - s
    print(f"fetch executed in {elapsed:0.2f} seconds.")
    result = {"responses": responses}
    return JsonResponse(result)


async def async_aggregation_from_external_view(request):
    # ok, but this is working
    responses = []
    async with httpx.AsyncClient() as client:
        for num in range(5):
            print("request: ", num)
            r = await client.get("https://python-podcast.de/api/?format=json")
            print("response: ", num)
            responses.append(r.json())
    result = {"responses": responses}
    return JsonResponse(result)


async def async_aggregation_from_external_experiment_view(request):
    url = "https://python-podcast.de/api/?format=json"
    start = time.time()
    responses = []
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[client.get(url) for x in range(5)])
        stop = time.time()
    print("took: ", start - stop)
    result = {"responses": responses}
    return JsonResponse(result)


def sync_external_api_view(request):
    responses = []
    r = httpx.get("https://python-podcast.de/api/?format=json")
    responses.append(r.json())
    result = {"responses": responses}
    return JsonResponse(result)


async def async_aggregation_view(request):
    responses = []
    async with httpx.AsyncClient() as client:
        r = await client.get("http://127.0.0.1:8000/async_api_view/")
    responses.append(r.json())
    result = {"responses": responses}
    return JsonResponse(result)


all_functions = get_all_functions(globals().copy())