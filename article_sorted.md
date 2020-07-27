# Django 3.1 Async

With [version 3.1](https://docs.djangoproject.com/en/3.1/topics/async/), you can
finally use asynchronous views, middlewares and tests in Django. Support for
async database queries will follow later. You don't have to change anything if
you don't want to use those new async features. All of your existing synchronous
code will run without modification in Django 3.1.

Async support for Django is on it's way for quite some time now. Since
[version 3.0](https://docs.djangoproject.com/en/3.0/releases/3.0/#asgi-support)
there's support for [ASGI](https://asgi.readthedocs.io/en/latest/) included. But
there was not much benefit for end users though. The only thing you could do
concurrently were file uploads, since uploads don't reach the view layer which
was not async capable in Django 3.0.

When do you might want to use those new features? If you are building
applications that have to deal with a high number of tasks simultaneously. Here
are some examples:

* Chat services like [Slack](https://slack.com)
* Gateway APIs / Proxy Services
* Games, especially MMOs like [Eve Online](https://www.eveonline.com/)
* Applications using [Phoenix Liveview](https://youtu.be/MZvmYaFkNJI) - check
  out [Phoenix Phrenzy results](https://phoenixphrenzy.com/results) for
  additional examples
* A reactive version of
  [Django Admin](https://docs.djangoproject.com/en/3.1/ref/contrib/admin/) where
  model changes are shown interactively
* A new api frontend for
  [Django REST framework](https://www.django-rest-framework.org/) updating list
  endpoints interactively as new data comes in
* All kinds of dashboard applications showing currently active connections,
  requests per second updating in realtime

As Tom Christie explained in his talk
[Sketching out a Django redesign](https://youtu.be/u8GSFEg5lnU) held at
DjangoCon 2019 the core question is this: Do we want to have to switch languages
to support those use cases? And while his [Starlette](https://www.starlette.io)
project (gaining popularity recently in combination with the
[FastAPI framework](https://fastapi.tiangolo.com)) is allowing us to do all this
in Python, we also might want to keep using Django.

## What to Expect from this Article?

1. Small example on how to use async views, middlewares and tests
2. Why is async such a big deal anyway?
3. The gory details of multithreading vs async, GIL and other oddities

# Part I - Async View Example

For this example you need a working installation of
[Python](https://www.python.org/). Any version from 3.6 onwards will do, but I
recommend using the latest 3.8 series, because async is relatively new to
Python and new versions still bring major improvements in usability and
stability.

## Create Virtualenv and Setup Project

Usually I prefer setting up new projects with
[Poetry](https://python-poetry.org/docs/) nowadays, but I understand that
requiring people to curl install software makes them feel uncomfortable. And for
this example it doesn't make a big difference anyway. Therefore I'll use the
builtin virtualenv module.

```shell
mkdir mysite && cd mysite
python -m venv mysite_venv && source mysite_venv/bin/activate  
python -m pip install django==3.1rc1 httpx  # install Django 3.1 + async capable http client
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
environment variable. This is what happens to me all the time.

## Create some Views

First we create a synchronous view returning a simple JsonResponse, just like we
would have done it in previous Django versions. It takes an optional parameter
`task_id` which we'll later use to identify the url which was called from the
second view. It also sleeps for a second emulating a response that takes some
time to be build.

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

### Async Aggregation View

Ok, let's add an asynchronous view then. We are creating a view that builds ten
different urls pointing to our original sync view and aggregate their results in
a new response.

Add this code to `mysite/views.py` and move the imports to the top of the file:
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

Add a route to our new view to `mysite/urls.py`:
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
called one after another summing up their latencies. But our async view took
only about one second to complete, so we must have called our sync views
concurrently by using `async def`, `async with` and the magic of
`asyncio.gather`. Great.


### Compare  with Sync View

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
    path("api/", views.api),
    path("api/aggregated/", views.api_aggregated),
    path("api/aggregated/sync/", views.api_aggregated_sync),
]
```

As expected, this
[sync aggregation view](http://127.0.0.1:8000/api/aggregated/sync/) takes now at
least ten seconds to finish. Fine.

### Why Did it Work?

But how did our async aggregation view work? Note that we just used the normal
builtin development server Django provides. Shouldn't we have to use some kind
of [ASGI](https://asgi.readthedocs.io/en/latest/) server?

Since we annotated our async view function with `async def` Django is able to
detect that we want to write an async view and runs our view in a thread within
its own [event loop](https://docs.python.org/3/library/asyncio-eventloop.html).
That's very convenient, because we could now write async views inside the normal
[WSGI](https://wsgi.readthedocs.io/en/latest/what.html) Django applications we
already use and they'll just work. We even gain the benefit of being able to do
things concurrently inside async views like fetching results from other api
endpoints and aggregating them in a new response.

What we won't get by running async views in a WSGI application is concurrency
when calling the view from the outside. Since each async view runs in it's own
thread, we'll still have as many threads as concurrent requests on any given
time.

### ASGI Example

To try out an async example that's concurrently callable from the outside, let's
install an ASGI server like [uvicorn](https://www.uvicorn.org/) then and change
the runserver command so that we are now running Django as an ASGI rather than a
WSGI application:

```shell
python -m pip install uvicorn
uvicorn --reload mysite.asgi:application
```

Our first [sync api view](http://localhost:8000/api/) still works as it should.
But if we try to open the
[async aggregated view](http://localhost:8000/api/aggregated/) view, we get a
timeout error. What is happening here? When the aggregated api view is called,
it makes subsequent get requests to ten sync api views. But uvicorn is a single
threaded server. The `httpx.get` tasks are dispatched to run asynchronously on
the event loop. But calls to `time.sleep` inside the sync api views are still
blocking the main thread, piling up to at least ten seconds latency. Since httpx
has a default timeout of five seconds, the fifth `httpx.get` call probably
raises an ReadTimeout exception in our async aggregation view causing the whole
view to fail.

In our previous `python manage.py runserver` example the `time.sleep` calls are
also blocking the threads they are running in. Since the development server is
running each request in it's own thread (it's multithreaded) the latencies
didn't add up but are blocking different threads concurrently. Therefore the
`httpx.get` calls only have to wait for about one second each.

If the backend you are sending requests to doesn't support answering those
requests concurrently, you still have to wait. We can resolve this by allowing
uvicorn to start more worker processes. But this would not guarantee that each
new request gets to run on a fresh worker. Maybe it's dispatched to a worker
which is already blocked by another request. So even if you have ten workers,
your aggregated response time will probably be larger than one second.

```shell
uvicorn --workers 10 mysite.asgi:application
```

But uvicorn is a async capable server, why don't we take advantage of this by
turning our sync api view into an async api view? You also have to move the
`import asyncio` line to the top of the file, if you haven't done this already:
```python
async def api(request):
    await asyncio.sleep(1)
    payload = {"message": "Hello Async World!"}
    if "task_id" in request.GET:
        payload["task_id"] = request.GET["task_id"]
    return JsonResponse(payload)
```

Note that you have to restart uvicorn to have your code changes take effect if
you are running uvicorn with multiple workers (with `--reload` you don't have to
restart uvicorn). Ok, now our
[async aggregated view](http://localhost:8000/api/aggregated/) should work again
as expected and our little example is async all the way down.

# Async Test Example

Now that we able to build async views, it would be really nice to be able to
test them asynchronously, too. Async test cases inherit from Django's normal
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

# Async Middleware Example

Here's an example adding a middleware which supports both sync
and async execution. Just add this code to `mysite/middleware.py`:
```python
import json
import time
import asyncio

from django.http import JsonResponse
from django.utils.decorators import sync_and_async_middleware


def add_elapsed_time(response, start):
    data = json.loads(response.content)
    data["elapsed"] = time.perf_counter() - start
    response = JsonResponse(data)
    return response


@sync_and_async_middleware
def timing_middleware(get_response):
    if asyncio.iscoroutinefunction(get_response):
        async def middleware(request):
            start = time.perf_counter()
            response = await get_response(request)
            response = add_elapsed_time(response, start)
            return response
    else:
        def middleware(request):
            start = time.perf_counter()
            response = get_response(request)
            response = add_elapsed_time(response, start)
            return response

    return middleware
```
This middleware just adds an elapsed field to every json response
to record the duration of each request.

To take effect, you also have to add this middleware to `mysite/settings.py`:
```python
MIDDLEWARE = [
    ...
    "mysite.middleware.timing_middleware",
]
```

You can check with your [async api view](http://localhost:8000/api/) and
[sync aggregation view](http://127.0.0.1:8000/api/aggregated/sync/) (you now
really have to increase the number of workers, otherwise you'll run into an
timeout) that your new middleware works in both cases.

# Part II - Why Async?

Concurrency via async is such a big deal, because it has two main advantages
over other approaches provided that your tasks are I/O bound:

1. It's more efficient
2. It's easier to write concurrent programs using async

## Resource Efficiency

What options do you have, when the number of tasks your application has to do
simultaneously increases? Let's have a look at the alternatives ordered from
high to low amount of effort:

* Spin up more machines
* Have your application use more cores on a single machine
* Use more operating system processes
* Start more operating system threads per process
* Use async/await to schedule multiple tasks in a single thread

If your tasks are CPU bound, you can only do more of them by adding more cores.
And if you use Python, the only way to use more cores is to add more operating
system processes. But most of the tasks we face when we build a website are not
CPU but I/O bound. Here are a some examples:

* Submitting sql queries to a database and fetching the result
* Aggregating answers from different API endpoints or microservices
* Getting a result from elasticsearch or a similar full text search service
* Fetching a site fragment from cache
* Loading some image from disk

When your browser sends a request to a website you'll wait some time until the
first byte is received. This time is critical to the perceived speed of a site,
because your browser won't do anything before that happened. But most of this
important time is not spend calculating the response, but waiting for some I/O
operation to complete. The speed of most websites could be improved dramatically
if all those blocking I/O calls would be replaced by non-blocking operations.

Instead of waiting in the application server for a database result you could use
an Ajax request in the browser to fetch this result later, for example. This
request will be then sent to your server and a complete application server
process will be blocked and waiting for the database to answer your query.
That's a lot of overhead for doing basically nothing.

And while using threads would be more efficient than using processes there's
still more overhead needed compared to using async tasks.

## Ease of Use

> Concurrency: one of the most difficult topics in computer science
> (usually best avoided).
> 
>  — David Beazley Python coach and mad scientist

Don't be fooled, writing concurrent programs using async/await is still harder
than writing synchronous ones. But it's not as hard as writing concurrent
programs using multiple threads. Why? [Because threads make local reasoning
difficult](https://glyph.twistedmatrix.com/2014/02/unyielding.html). You can't
just take a function and think about whether the code in there makes sense in
isolation. You have to keep in mind all the other code which might be running
concurrently interfering with the code in the function you are looking at. In
this respect threads have a
[daunting similarity to goto statements](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/).
Python threads are operating system threads and the OS kernel gets to decide
which threads is scheduled to run. Therefore you simply don't know when the flow
of control will be transferred to another thread. It could happen any time.

Async tasks are different. They use cooperative multitasking where each tasks
decides on it's own when it's time to give up control. As long as you won't use
the `await` keyword to
[signal that now other tasks might be executed](https://hynek.me/articles/waiting-in-asyncio/)
concurrently your code runs sequentially just like a normal synchronous program.
Which means that if you call blocking I/O functions or hog the CPU with long
running calculations, no other task will get the chance to run. Therefore you
have to know whether a function you calls other functions that might block. And
if you are doing I/O that would be awaitable you have to mark your function
awaitable with `async def`, which is a little bit like writing Python
[using explicitly enforced typing](https://www.encode.io/articles/python-async-frameworks-beyond-developer-tribalism).
It's harder because you have to be more precise about what kind of things your
code is doing. Therefore multithreading will look easier if you simply count the
lines you'd have to change to transform a single task application into one which
is able to run multiple tasks concurrently. But the additional effort in code
lines if you take the async route will probably worthwhile in the long run.

And while writing concurrent programs using asyncio is easier than using
multiple threads there's still room for improvement. There's
[Curio](https://github.com/dabeaz/curio) for example. Or
[Trio](https://trio.readthedocs.io/en/stable/) inspired by Curio which is using
nurseries to get rid of futures which remain an obstacle to local reasoning
about code in asyncio.

## Async Adapter Functions

Ok, using async tasks to do things concurrently seems to be reasonable. But what
about the ORM and other parts of Django which are not async capable yet? Is
there a way to fetch models from the database without blocking all other async
tasks? Fortunately there are two
[adapter functions](https://docs.djangoproject.com/en/3.1/topics/async/#async-adapter-functions)
helping us to deal with situations like this.

Let's say we want to fetch a model from the database while being in an async
view function. Then we can wrap our model fetching function in a
`sync_to_async()` call which will then return a coroutine we can await. Other
async tasks are still running concurrently, because the calling async view
awaiting the wrapped sync function will be guaranteed to run in an event loop on
a different thread. By default the called sync function will be executed in a
newly created thread. But sometimes (accessing sqlite for example) you need to
pass `thread_sensitive=True` to force the called sync function to be executed on
the main thread instead.

And sometimes it's the other way around and you need to make a call to an async
function from a sync one. This is basically the same situation you encounter
when writing an async program from scratch. Usually you would use
`asyncio.run(my_coroutine)` to start an event loop managing calls to your async
functions. In Django you'll wrap your async function in a call to
`async_to_sync()` which will take care of setting up the event loop but also
makes sure threadlocals will work.

# Part III - Additional Details

I stumbled about a lot of quirks and oddities while writing this article, and
this is the place to share them :).

## A little bit of History

Historically, async programming via explicit coroutines is the newest paradigm
trying to make writing concurrent programs easier. The asyncio standard library
module was added to Python 3.4 in 2014. The keywords `async` and `await` were
first introduced in Python 3.5 one and a half year later, adding native language
support for async functions. But even Python 3.5 seems to be hard to support, as
most of the async native libraries and web frameworks like Curio, Trio and
Starlette require at least Python 3.6 in the meantime.

Django's async story started about two years ago as Andrew Godwin proposed
[A Django Async Roadmap](https://www.aeracode.org/2018/06/04/django-async-roadmap/).
It only made sense to support the new async syntax after dropping support for
Python 3.4 which happened with Django 2.1. One year ago,
[DEP 0009: Async-capable Django](https://github.com/django/deps/blob/master/accepted/0009-async.rst)
was
[approved](https://groups.google.com/forum/#!msg/django-developers/5CVsR9FSqmg/UiswdhLECAAJ)
by the technical board. It's already a pretty detailed plan on how to move
Django from sync-only to native async with sync wrapper. End of 2019
[Django 3.0](https://docs.djangoproject.com/en/3.0/releases/3.0/) was released
(requiring at least Python 3.6) adding support for ASGI. The gap between the
first Django version which could have supported async hypothetically (2.1) and
the version which started supporting async (3.0) is not that big, to say the
least.

## Concurrency vs Parallelism

> Concurrency is about dealing with lots of things at once.
> Parallelism is about doing lots of things at once.
> Not the same, but related. One is about structure, one is about
> execution. Concurrency provides a way to structure a solution to
> solve a problem that may (but not necessarily) be parallelizable.
> 
> — Rob Pike Co-inventor of the Go language

The quote above may (but not necessarily) be helpful to understand the
difference between concurrency and parallelism. I found another example to be
more helpful: Think of a bartender serving customers. One single bartender is
capable of preparing multiple drinks and therefore serving multiple customers
concurrently. But he's still doing one step after another. If multiple drinks
have to be created in parallel, you need multiple bartenders.

Doing things concurrently on a computer is possible, even if you only have one
CPU executing instructions step by step. But it's not possible to do multiple
tasks at the same time without using multiple CPUs. And because of the infamous
[GIL](https://www.dabeaz.com/python/UnderstandingGIL.pdf), it's impossible to do
things on multiple CPUs using only one OS process. Contrary to popular belief
this is not a unique feature of Python, but also present in Ruby, NodeJS and
PHP. All those languages use reference counting for memory management and it's
impossible ([or nearly impossible](https://lwn.net/Articles/689548/)) to use
reference counting without a GIL without being at least an order of magnitude
slower. Java uses a different kind of automatic memory management and therefore
has no need for a GIL. But Java has to pay a price in slower single thread
performance (what most users should care about, since most software is not
running on multiple CPUs in parallel) and unpredictable latency. It's just a
different set of tradeoffs which might or might not fit your use case.

## Scalability

It's often said that threads are not as scalable as async tasks, because they
tend to use more memory or hog the CPU because of all the context switches they
are causing. I'm at least a bit skeptical about such claims. Under investigation
they often turn out to be not true or not true anymore. The default stack size
for a new thread on linux and macOS (`ulimit -s`) is 8MB. But that doesn't mean
this is the real memory overhead of starting an additional thread. First off,
it's virtual memory and not resident, and second - yes, while this imposed a
hard and low limit on the number of threads on 32bit machines (usable virtual
memory is only 3GB), on 64bit machines this limit is no longer relevant. Here's
an article describing that
[running 10k threads](https://eli.thegreenplace.net/2018/measuring-context-switching-and-memory-overheads-for-linux-threads/)
should be not a big problem on current hardware. But while starting 10k threads
on linux worked as expected, on macOS this little script lead to a reproducible
kernel panic:

```python
import time

import concurrent.futures


def do_almost_nothing(task_id):
    time.sleep(5)
    return task_id


num_tasks = 10000
results = []
s = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=num_tasks) as executor:
    future_to_function = {}
    for task_id in range(num_tasks):
        future_to_function[executor.submit(do_almost_nothing, task_id)] = task_id
    for future in concurrent.futures.as_completed(future_to_function):
        function = future_to_function[future]
        try:
            results.append(future.result())
        except Exception as exc:
            print('%r generated an exception: %s' % (function, exc))
elapsed = time.perf_counter() - s
print(f"do_almost_nothing executed in {elapsed:0.2f} seconds.")
```

Async tasks on the other hand only take about 2KB memory each and are more or
less just one function call. Ok, that's hard to beat. Use this snippet to
measure for yourself:

```python
import time
import asyncio


async def do_almost_nothing(task_id):
    await asyncio.sleep(5)
    return task_id


async def main():
    num_tasks = 1000000
    tasks = []
    for task_id in range(num_tasks):
        tasks.append(asyncio.create_task(do_almost_nothing(task_id)))
    responses = await asyncio.gather(*tasks)
    print(len(responses))


asyncio.run(main())
```

Threads also did suffer from a lock contention problem on Python 2. The Python
interpreter checked every 100 ticks if another thread should be able to acquire
the GIL. This leads to slower performance even on a single CPU, but on on
machines with multiple cores this was especially bad, because now threads would
fight over getting the GIL on different CPUs in parallel. Those issues were
fixed with the new GIL introduced in Python 3.2 and now check gets only called
every 5ms (it's configurable via sys.setswitchinterval).

# One final Example

After deciding to write something about the upcoming support of async views in
Django 3.1, I was looking for a compelling example to show off the benefits of
async views. Chat is not a good example because you probably would use
websockets to implement a chat site nowadays. But you'll need
[Django Channels](https://channels.readthedocs.io/en/latest/) for websocket
support since support for protocols other than http will continue to stay in
Channels. Finally I settled on an async view aggregating results from multiple
other api endpoints. But do you really need Django 3.1 and async views to be
able to write a view like this?

Let's add this view to our `mysite/views.py`file:
```python
import concurrent.futures


def api_aggregated_threadpool(request):
    s = time.perf_counter()
    results = []
    urls = get_api_urls()
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

And connect this view to an url adding a route to `mysite/urls.py`:
```python
urlpatterns = [
    path("api/", views.api),
    path("api/aggregated/", views.api_aggregated),
    path("api/aggregated/sync/", views.api_aggregated_sync),
    path("api/aggregated/threadpool/", views.api_aggregated_threadpool),
]
```

Start your local WSGI server with `python manage.py runserver` and have a look
at the [result](http://localhost:8000/api/aggregated/threadpool/). If you just
want to aggregate some request results concurrently a threadpool will probably
sufficient. You won't have to use a different application server supporting ASGI
and this works also for older Django versions.

# Credits

Thanks to Klaus Bremer and Simon Schliesky for reading drafts of this.