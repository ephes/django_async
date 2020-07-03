# Summary

There seems to be an issue when you try to connect from an async view
inside an asgi server to a sync view served by the same asgi server
your view is running in. Doing this in a normal wsgi server works just
fine. And since all asgi servers I tried behave the same, I assume it's
a misunderstanding on my side. But nevertheless I'd like to understand
what's going on here.

# Howto Reproduce

## Install Poetry and Setup Project
```shell
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
mkdir foobar
cd foobar
poetry init   # just press enter a lot
poetry add django==3.1b1 uvicorn httpx daphne hypercorn
poetry shell  # switch to virtualenv created by poetry, I have to use a new shell, dunny why
```

## Initialize Django
```shell
django-admin startproject foobar .  # create django project in current directory
python manage.py migrate            # migrate sqlite
python manage.py runserver          # should start the development server now
```

## Create some Views

Edit foobar/views.py to look like this:
```python
import httpx

from django.http import JsonResponse


def sync_api_view(request):
    payload = {"foo": "bar"}
    return JsonResponse(payload)


async def async_api_view(request):
    payload = {"foo": "bar"}
    return JsonResponse(payload)


def sync_aggregation_view(request):
    responses = []
    r = httpx.get("http://127.0.0.1:8000/sync_api_view/")
    responses.append(r.json())
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
```

And foobar/urls.py like this:
```python
from django.urls import path

from . import views

urlpatterns = []  # add all functions ending with "view" to urlpatterns
for view in dir(views):
    if view.endswith("view"):
        urlpatterns.append(path(view + "/", getattr(views, view)))
```

## Debug

### Standard Development Server

Starting the standard Django development server, all views work as expected:
``` shell
python manage.py runserver

for view in sync_api_view async_api_view sync_aggregation_view sync_external_api_view async_aggregation_view                                                                                                                    
    open "http://localhost:8000/$view/"
end
```

### Using asgi Uvicorn Server
All views work except the one connecting from a sync view back to itself
fetching a result from an async view.

``` shell
uvicorn foobar.asgi:application

for view in sync_api_view async_api_view sync_aggregation_view sync_external_api_view async_aggregation_view                                                                                                                
    open "http://localhost:8000/$view/"
end
```

It just throws an exception looking like this:
```
Exception Type: ReadTimeout at /sync_aggregation/
Exception Value: timed out
```

Using daphne or hypercorn results in the same error. So it's not an issue
with uvicorn rather than a misunderstanding on my side.