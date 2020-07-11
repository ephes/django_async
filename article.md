# Django 3.1 Async

Async support for Django is on it's way for quite some time now. Since
[version 3.0](https://docs.djangoproject.com/en/3.0/releases/3.0/#asgi-support) there's support for [ASGI](https://asgi.readthedocs.io/en/latest/) included. There was not much improvements from using asgi for
the end user though. The only thing you could do was to have the handler handle multiple file uploads in an async matter, since file uploads don't reach the view layer which is not async in Django 3.0.

In Django 3.1 it will be possible have async middlewares, async tests and real async views. That opens up a lot of interesting opportunities.

## Django Async History

Five/Six years ago Andrew Godwin after working on migrations for Django started the [channels](https://github.com/django/channels/) project. It's about adding support for non http protocols (websockets/webrtc) to Django.

About two years ago Andrew Godwin proposed
[A Django Async Roadmap](https://www.aeracode.org/2018/06/04/django-async-roadmap/) to bring async functionality to Django. Since Version 2.1 Django
would only support Python 3.5 and up which includes native syntax/support
for coroutines (async def). For Django > 3 it's even Python 3.6
upwards. Adding async support for Django while it was still supporting
Python 2 would have made no sense at all.

One year ago, [DEP 0009: Async-capable Django](https://github.com/django/deps/blob/master/accepted/0009-async.rst) was [approved](https://groups.google.com/forum/#!msg/django-developers/5CVsR9FSqmg/UiswdhLECAAJ) by the technical board.
It's already a pretty detailed plan on how to move Django from sync-only to
native async with sync wrapper.

End of 2019 [Django 3.0](https://docs.djangoproject.com/en/3.0/releases/3.0/) was released adding support for ASGI.

In August 2020 [Django 3.1 will be released](https://learndjango.com/tutorials/whats-new-django-31) which will include support for async middlewares, async testing and finally async views.

# Threads vs Async

> Concurrency is about dealing with lots of things at once.
> Parallelism is about doing lots of things at once. Not the same,
> but related. One is about structure, one is about execution.
> Concurrency provides a way to structure a solution to solve
> a problem that may (but not necessarily) be parallelizable.
> 
> — Rob Pike Co-inventor of the Go language

If we talk about Django async support we almost always mean concurrency
and not parallelism. Yes, we are answering requests in parallel if
we run a webserver with multiple worker processes, but usually our
application server takes care of this and we don't have to worry
about this stuff as application developers.

All our problems are io-bound.

# Points

* GIL gets released automaticall on io context switch
* Trio 

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