# Django 3.1 Async Views

In Django 3.1 it's possible have real async views.

# Why

* Handling long-lived network connections like Websockets.
* Long-lived HTTP connections and server sent events.
* Dealing with background tasks without necessarily needing a full blown task queue subcomponent.
* Parallelizing outgoing HTTP requests or other high latency I/O.

https://www.encode.io/articles/python-async-frameworks-beyond-developer-tribalism?utm_campaign=Django%2BNewsletter&utm_medium=web&utm_source=Django_Newsletter_30

# Example Project

## Install Poetry and Setup Project
```shell
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
mkdir mysite && cd mysite && poetry init -n
poetry add django==3.1b1 httpx
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

from django.http import JsonResponse


def api(request):
    time.sleep(1)
    payload = {"message": "Hello World!", "task_id": request.GET.get("task_id")}
    return JsonResponse(payload)


async def api_aggregated(request):
    responses = []
    base_url = "http://127.0.0.1:8000/sync/api/"
    urls = [f"{base_url}?task_id={task_id}" for task_id in range(10)]
    s = time.perf_counter()
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[client.get(url) for url in urls])
        responses = [r.json() for r in responses]
    elapsed = time.perf_counter() - s
    result = {
        "responses": responses,
        "debug_message": f"fetch executed in {elapsed:0.2f} seconds."
    }
    return JsonResponse(result)
```

And mysite/urls.py like this:
```python
from django.urls import path

from . import views

urlpatterns = [
    path("sync/api/", views.api),
    path("async/api_aggregated/", views.api_aggregated),
]
```

You can check it's working by pointing your browser at [sync_api](http://localhost:8000/sync/api)
and [async_aggregation](http://localhost:8000/async/api_aggregated/)