# Django 3.1 Async

With this shiny new version, you can finally use asynchronous views, middlewares
and tests in Django. You don't have to change anything when you don't want to
use async views. In Django 3.1 all of your existing code will run without the
need for any modification.

1. Small example on how to use views / middlewares / tests
2. What are async views good for
3. Comparison with other techniques (multithreading etc)

# Async View Example

For this example you need a working installation of
[Python](https://www.python.org/). Any version from 3.6 onwards should work, but
I would recommend to use the latest 3.8 series, because since async is
relatively new to Python new versions bring major improvements.

## Create Virtualenv and Setup Project

Usually I prefer setting up new projects with
Poetry](https://python-poetry.org/docs/) nowadays, but I understand that
requiring people to curl install stuff makes them feel uncomfortable. And for
this example there's not much of a difference anyway. Therefore I'll use the
builtin virtualenv module throughout this example.

```shell
mkdir mysite && cd mysite
python -m venv mysite_venv && source mysite_venv/bin/activate  
python -m pip install django==3.1b1 httpx
```

## Initialize Django
```shell
django-admin startproject mysite .  # create django project in current directory
python manage.py migrate            # migrate sqlite
python manage.py runserver          # should start the development server now
```

You should now be able to point your browser to
[localhost](http://localhost:8000/) and see the new Django project sample page.
If this doesn't work, make sure you didn't set the $DJANGO_SETTINGS_MODULE
environment variable. This happens to me all the time.

## Create some Views

First we create a synchronous view named returning a simple JsonResponse, just
like we would have done it in previous Django versions. It takes an optional
parameter `task_id` which we'll later use to identify the url which was called
from the second view. It also sleeps for a second emulating a response that
takes some time to be build.

Edit `mysite/views.py` to look like this:
```python
import time

from django.http import JsonResponse


def api_sync(request):
    time.sleep(1)
    payload = {"message": "Hello World!"}
    if "task_id" in request.GET:
        payload["task_id"] = request.GET["task_id"]
    return JsonResponse(payload)
```

And then edit `mysite/urls.py`to look like this:
```python
from django.urls import path

from . import views

urlpatterns = [
    path("api/sync/", views.api_sync),
]
```

Now you should be able to see the response of little api view in your
[browser](http://localhost:8000/api/sync/). I would recommend
[Firefox](https://firefox.org/) to look at json responses because they look a
little bit nicer there, but any browser will do. This is not at all different
from a normal synchronous api view in Django before 3.1.

Ok, let's add an asynchronous view then. We are creating a view that builds ten
different urls pointing to our original sync view and aggregate their results in
a new response.

Add this async def view to
`mysite/views.py`:
```python
import httpx
import asyncio

async def api_aggregated(request):
    responses = []
    base_url = "http://127.0.0.1:8000/api/sync/"
    urls = [f"{base_url}?task_id={task_id}" for task_id in range(10)]
    s = time.perf_counter()
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[client.get(url) for url in urls])
        responses = [r.json() for r in responses]
    elapsed = time.perf_counter() - s
    print(responses)
    result = {
        "message": "Hello Async World!",
        "responses": responses,
        "debug_message": f"fetch executed in {elapsed:0.2f} seconds.",
    }
    return JsonResponse(result)
```

And a route to the new aggregated view to `mysite/urls.py`:
```python
urlpatterns = [
    path("api/sync/", views.api_sync),
    path("api/aggregated/", views.api_aggregated),
]
```

Now you should be able to see the result of your first asynchronous view
in your [browser](http://localhost:8000/api/aggregated/). 


You can check it's working by pointing your browser at
[sync_api](http://localhost:8000/api) and
[async_aggregation](http://localhost:8000/api_aggregated/).
