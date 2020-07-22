# Django 3.1 Async

With this new version, you can finally use asynchronous views, middlewares and
tests in Django. You don't have to change anything when you don't want to use
those async features. In Django 3.1 all of your existing code will run without
need for modification.

What to expect from this article?

1. Small examples on how to use views / middlewares / tests
2. What are async views good for
3. Comparison with other techniques (multithreading etc)

# Async View Example

For this example you need a working installation of
[Python](https://www.python.org/). Any version from 3.6 onwards will do, but I
recommend to use the latest 3.8 series, because async is relatively new to
Python and new versions still bring major improvements in usability and
stability.

## Create Virtualenv and Setup Project

Usually I prefer setting up new projects with
Poetry](https://python-poetry.org/docs/) nowadays, but I understand that
requiring people to curl install stuff makes them feel uncomfortable. And for
this example there's not much of a difference anyway. Therefore I'll use the
builtin virtualenv module throughout this example.

```shell
mkdir mysite && cd mysite
python -m venv mysite_venv && source mysite_venv/bin/activate  
python -m pip install django==3.1rc1 httpx
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


def api(request):
    time.sleep(1)
    payload = {"message": "Hello World!"}
    if "task_id" in request.GET:
        payload["task_id"] = request.GET["task_id"]
    return JsonResponse(payload)
```

And then `mysite/urls.py` to look like this:
```python
from django.urls import path

from . import views

urlpatterns = [
    path("api/", views.api),
]
```

Now you should be able to see the response of little
[api view](http://localhost:8000/api/) in your browser. I recommend
[Firefox](https://firefox.org/) to look at json responses because they look a
little bit nicer there, but any browser will do. This is not at all different
from a normal synchronous api view in Django before 3.1.

Ok, let's add an asynchronous view then. We are creating a view that builds ten
different urls pointing to our original sync view and aggregate their results in
a new response.

Add this async def view to `mysite/views.py`:
```python
import httpx
import asyncio


def get_api_urls(num=10):
    base_url = "http://127.0.0.1:8000/api/"
    return [f"{base_url}?task_id={task_id}" for task_id in range(num)]


async def api_aggregated(request):
    s = time.perf_counter()
    responses = []
    urls = get_api_urls(num=10)
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[client.get(url) for url in urls])
        responses = [r.json() for r in responses]
    elapsed = time.perf_counter() - s
    result = {
        "message": "Hello Async World!",
        "responses": responses,
        "debug_message": f"fetch executed in {elapsed:0.2f} seconds.",
    }
    return JsonResponse(result)
```

Add a route to the new aggregated view to `mysite/urls.py`:
```python
urlpatterns = [
    path("api/", views.api),
    path("api/aggregated/", views.api_aggregated),
]
```

If you now point your browser to the url of your
[aggregated view](http://localhost:8000/api/aggregated/), you should be able to
see your first result from an asynchronous function. A normal sync view calling
`httpx.get(url)` in a for loop would have taken at least ten seconds to
complete, because every api view sleeps for one second and they would have been
called one after another and their latencies are just summing up. But our async
view took only about one second to complete, so we must have called our sync
views concurrently by using `async def`, `async with` and the magic of
`asyncio.gather`. Great.

We can check our hypothesis by adding a plain sync aggregation view to `mysite/views.py`:
```python
def api_aggregated_sync(request):
    s = time.perf_counter()
    responses = []
    urls = get_api_urls(num=10)
    for url in urls:
        r = httpx.get(url)
        responses.append(r.json())
    elapsed = time.perf_counter() - s
    result = {
        "message": "Hello Sync World!",
        "aggregated_responses": responses,
        "debug_message": f"fetch executed in {elapsed:0.2f} seconds.",
    }
    return JsonResponse(result)
```

And also add a route to the sync aggregated view to `mysite/urls.py`:
```python
urlpatterns = [
    path("api/", views.api_sync),
    path("api/aggregated/", views.api_aggregated),
    path("api/aggregated/sync/", views.api_aggregated_sync),
]
```

As expected, this
[sync aggregation view](http://127.0.0.1:8000/api/aggregated/sync/) takes now at
least ten seconds to finish. Fine. But how did this work? Note that we just used
the normal builtin development server Django provides. Shouldn't we have to use
some kind of [ASGI](https://asgi.readthedocs.io/en/latest/) server?

Since we annotated our async view function with `aync def` Django is able to
detect that we want to write an async view and runs our view in a thread within
its own [event loop](https://docs.python.org/3/library/asyncio-eventloop.html).
That's very convenient, because we could now write async views inside the normal
[WSGI](https://wsgi.readthedocs.io/en/latest/what.html) Django applications we
are already using and they'll just work. We even gain the benefit of being able
to do things concurrently inside async views like fetching results from other
api endpoints and aggregating them in a new response.

What we won't get by running async views in a WSGI application is concurrency
when calling the view from the outside. Since each async view runs in it's own
thread, we'll still have as many threads as concurrent requests at a time. Ok
let's install an ASGI server like [uvicorn](https://www.uvicorn.org/) then and
change the runserver command so that we are now running Django as an ASGI rather
than as a WSGI application:

```shell
python -m pip install uvicorn
uvicorn mysite.asgi:application
```

Our normal [sync api view](http://localhost:8000/api/) still works normally. But
if we try to open the
[async aggregated view](http://localhost:8000/api/aggregated/) view, we get a
timeout error. What is happening here? When the aggregated api view is called,
it makes subsequent calls to ten sync api views. But uvicorn is a single
threaded server by default. The main thread responsible for serving the async
aggregation view is calling itself to answer the sync api view requests creating
a deadlock which is then resolved by throwing the ReadTimeout after some time.

We can resolve this deadlock by allowing uvicorn to start more workers:

```shell
uvicorn --workers 10 mysite.asgi:application
```

Or more elegantly, changing our sync api view into an async api view. You have
to move the `import asyncio` line to the top of the file, if you haven't done
this already:
```python
async def api(request):
    await asyncio.sleep(1)
    payload = {"message": "Hello Async World!"}
    if "task_id" in request.GET:
        payload["task_id"] = request.GET["task_id"]
    return JsonResponse(payload)
```

Note that you have to restart uvicorn to have your code changes take effect. A
future version of the Django development server might include an ASGI capable
version so this would not be necessary. Or you could use
[daphne](https://github.com/django/daphne) from the
[Django Channels](https://channels.readthedocs.io/en/latest/) project which also
does reload on code changes. Ok, now our
[async aggregated view](http://localhost:8000/api/aggregated/) should work
again.

# Async Test Example

Not that we able to build async views, it would be really nice to be able to
test them asynchronously, too. Async test cases inherit from Djangos normal
TestCase base class. But you have to mark async test methods as `async def` to
be able to `await` responses. In addition to the synchronous Django test client
there's now an AsyncClient. 

To add a simple test for our api view edit `mysite/test_views.py`:
```python
from django.test import TestCase
from django.test import AsyncClient


class TestApiWithClient(TestCase):
    async def test_api_with_async_client(self):
        client = AsyncClient()
        response = await client.get("/api/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual("Hello Async World!", data["message"])
```

Then run the test using django-admin:
```shell
python manage.py test
```

If you don't want to use a full http client, there's an AsyncRequestFactory,
too.
