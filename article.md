# Django 3.1 Async

Async support for Django is on it's way for quite some time now. Since
[version 3.0](https://docs.djangoproject.com/en/3.0/releases/3.0/#asgi-support) there's support for [ASGI](https://asgi.readthedocs.io/en/latest/) included. There was not much improvements from using asgi for
the end user though. The only thing you could do was to have the handler handle multiple file uploads in an async matter, since file uploads don't reach the view layer which is not async in Django 3.0.

In Django 3.1 it will be possible have async middlewares, async tests and real async views. That opens up a lot of interesting opportunities.

## Django Async History

Five/Six years ago Andrew Godwin, after working on migrations, for Django started the [channels](https://github.com/django/channels/) project. It's about adding support for non http protocols (WebSockets/WebRTC/MQTT) to Django.

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

# Concurrency

> Concurrency is about dealing with lots of things at once.
> Parallelism is about doing lots of things at once. Not the same,
> but related. One is about structure, one is about execution.
> Concurrency provides a way to structure a solution to solve
> a problem that may (but not necessarily) be parallelizable.
> 
> — Rob Pike Co-inventor of the Go language

If we talk about Django async support we almost always mean concurrency
and not parallelism. Yes, it's possible for Django powered webservers 
to process multiple requests in parallel. But those requests will
be running in different worker processes and their interactions usually
only take place in the databases which uses transactions for isolation.

## GIL

While in other languages it might be possible that one operating
system process does multiple things on different CPUs in parallel,
in python it's not, because of the infamous
[GIL](https://www.dabeaz.com/python/UnderstandingGIL.pdf). Contrary
to popular belief this is not a unique feature of Python, but also
present in Ruby, NodeJS and PHP. All those languages use reference
counting for memory management and it's impossible
([or nearly impossible](https://lwn.net/Articles/689548/)) to use
reference counting without something like a GIL without being at
least an order of magnitute slower. Java for example uses a
different kind of automatic memory management and therefore has no
need for a GIL. But Java has to pay a price in slower single thread
performance (what most users should care about, since most software
is not multithreaded) and unpredictable latency. It's just a
different set of tradeoffs.

## Concurrent I/O

> Python threads are great at doing nothing.
> 
>   — David Beazley Python coach and mad scientist

Maybe it's time for an example. Being contraint by the
GIL does not mean we couldn't do things concurrently in
a single Python process. Let's say we want to fetch
information about five star wars characters from an external
api. At first we build a list of urls we want to retrieve:

```python
import time
import httpx

base_url = "https://swapi.dev/api/people"
urls = []
for character_id in range(1, 6):
    urls.append(f"{base_url}/{character_id}/")
```

### Sync Requests
Now we have to fetch those urls. The first thing that comes
to mind is to just use sync requests.

```python
s = time.perf_counter()
for url in urls:
    r = httpx.get(url)
    print(r.json()["name"])
elapsed = time.perf_counter() - s
print(f"fetch executed in {elapsed:0.2f} seconds.")
```

This takes for about 0.35s on my machine. But most of the
time the code is just waiting for swapi.dev to answer the
http get requests. And while it's waiting, nothing else is
happening. Each request takes about 70ms and therefor it
takes 350ms to complete all five requests.

### Multithreading
Can we do better?
```python
import concurrent.futures

s = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    future_to_url = {executor.submit(httpx.get, url): url for url in urls}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            r = future.result()
            print(r.json()["name"])
        except Exception as exc:
            print('%r generated an exception: %s' % (url, exc))
elapsed = time.perf_counter() - s
print(f"fetch executed in {elapsed:0.2f} seconds.")
```
Much better - this only takes about 140ms. Instead of waiting for
each request to complete, we just fire up a new thread for each url
and wait until they all have completed. Now the time it takes to
complete all requests is not sum(all_requests) but abs(slowest_request).
Why does this work? Doesn't the GIL prevent us from doing things in
parallel? Yes, but the GIL is automatically released when a thread
blocks on I/O.

### Async
Now there's another option to multiplex I/O without creating operating
system threads. We could use the relatively new async function syntax
and asyncio to fetch those urls concurrently:

```python
import asyncio

s = time.perf_counter()
async with httpx.AsyncClient() as client:
    responses = await asyncio.gather(*[client.get(url) for url in urls])
    for r in responses:
        print(r.json()["name"])
elapsed = time.perf_counter() - s
print(f"fetch executed in {elapsed:0.2f} seconds.")
```
This yields about the same performance as the threading solution.

## Theads vs Async

Ok, threads and async both seem to be fine, so which one should
be used? It depends.

### Multitasking

Doing things concurrently means we would like to do some kind of
multitasking. When we are creating threads to achieve this, we
employ a form of preemptive multitasking, because the operating
system kernel has to decide which thread get's interrupted when
and which other thread is scheduled to run now. In multithreading
control switches between threads all the time and even if one
thread gets stuck it probably wont affect other running threads
much.

In the async world, on the other hand, we have a form of cooperative
multitasking where the application code itself gets to decide when
it yields control back to other tasks. Which also means that
if a async task blocks, it blocks all other tasks too.

### Scalability

It's often said that thread are not as scalable as async tasks,
because they tend to use more memory or hog the CPU because of
all the context switches they are causing. I'm at least a bit
sceptical about such claims. Under investigation they often turn
out to be not true or not true anymore. The default stack size
for a new thread on linux and macOS (`ulimit -s`) is 8MB. But
that doesn't mean this is the real memory overhead of a thread.
First off, it's virtual memory and not resident, and second -
yes, while this imposed a hard and low limit on the number of
threads on 32bit machines (usable virtual memory is only 3GB),
on 64bit machines this limit is no longer relevant. Here's an
article describing that 
[running 10k threads](https://eli.thegreenplace.net/2018/measuring-context-switching-and-memory-overheads-for-linux-threads/)
should be not a big problem on current hardware.

Async tasks only take about 1KB memory and are more or less just
one function call. Ok, that's hard to beat.

### Difficulty

> Concurrency: one of the most difficult topics in computer science
> (usually best avoided).
> 
>  — David Beazley Python coach and mad scientist

Concurrent programs are more difficult to write than normal ones.
But getting multithreaded programs right is especially difficult.
Since task switching can happen any time, it's really hard to
find out where things did go wrong. Let's say you have one thread
which is responsible for moving money between bank accounts. If
it gets interrupted while in the midst of transferring money from
a to b maybe the money was added to account b, but not yet deleted
from account a. It's now possible for another thread to move the
same money from a to c which was already added to b. That's not good.
Therefore you have to be careful to protect shared ressources with
locks or use other mechanisms to avoid those situations. So the
default case for multithreading is that control can switch at any
point in the code except for those parts that were explicitly
protected by locks. 

Async programs seem to be more easy to reason about because they
do it the other way around. The default case in an async task is
that there's no way other tasks are getting control at a random
line. All lines where control could be transferred to another task
are explicitly marked with `await`. So the number of points where
things can go wrong in a hard to debug way is a lot lower.

# Points

* Trio got rid of futures
* Traditional approaches to handle concurrent programming tend to be frightingly similar to goto
* With threads, you usually have to be careful about shared ressources and lock accordingly because of preemptive multitasking can take over control at every moment. With async all code is "locked" by default and you explicitly mark those parts of the code where other stuff can happen (await)
* Daphne (channels 1) was running on twisted, now you can use any asgi server

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