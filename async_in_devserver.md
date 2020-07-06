# Django 3.1 Async Views Working in Development Server?

Seems that async views are working without having to start servers
like uvicorn.

# Install Poetry and Setup Project
```shell
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
mkdir mysite && cd mysite && poetry init -n
poetry add django==3.1b1 httpx
poetry shell  # switch to virtualenv created by poetry, I have to use a new shell, dunny why
```

# Initialize Django
```shell
django-admin startproject mysite .  # create django project in current directory
python manage.py migrate            # migrate sqlite
python manage.py runserver          # should start the development server now
```

# Create some Views

Edit mysite/views.py to look like this:
```python
import time
import httpx
import asyncio

from django.http import JsonResponse

def api(request):
    time.sleep(1)
    payload = {"hello": "world"}
    return JsonResponse(payload)


async def aggregate_sync_api(request):
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
```

And mysite/urls.py like this:
```python
from django.urls import path

from . import views

urlpatterns = [
    path("sync/api/", views.api),
    path("async/aggregate_sync_api/", views.aggregate_sync_api),
]
```

And now, to my surprise, this just works:
```shell
open localhost:8000/async/aggregate_sync_api/
```