# Django 3.1 Async Views

In Django 3.1 it's possible have real async views.

# Example Project

## Install Poetry and Setup Project
```shell
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
mkdir mysite && cd mysite && poetry init -n
poetry add django==3.1b1 uvicorn httpx
poetry shell  # switch to virtualenv created by poetry, I have to use a new shell, dunny why
```

## Initialize Django
```shell
django-admin startproject mysite .  # create django project in current directory
python manage.py migrate            # migrate sqlite
python manage.py runserver          # should start the development server now
```

## Create some Views

Edit mysite/views.py to look like this:
```python
import time
import httpx
import asyncio
import concurrent.futures

from django.http import JsonResponse

def api(request):
    time.sleep(1)
    payload = {"hello": "world"}
    return JsonResponse(payload)


async def aggregate_sync_view(request):
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
```

And mysite/urls.py like this:
```python
from django.urls import path

from . import views

urlpatterns = [
    path("sync/api/", views.api),
    path("async/aggregate_sync_view/", views.aggregate_sync_view),
]
```