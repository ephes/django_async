# Install Poetry
```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
```

# Setup Project

```
mkdir foobar
cd foobar
```

Create pyproject.toml - Just press enter for the questions.
```
poetry init
```

Install dependencies
```
poetry add django==3.1b1 uvicorn httpx
```

Switch into the virtualenv created by poetry
```
poetry shell
```

Create your django project in the current directory
```
django-admin startproject foobar .
```

Migrate sqlite
```
python manage.py migrate
```

Start standard development server
```
python manage.py runserver
```

Start uvicorn
```
python manage.py runserver
```

# Debug

Works in both devserver and uvicorn, even as  async def view.
```
from django.http import JsonResponse


def sync_api_view(request):
    payload = {"foo": "bar"}
    return JsonResponse(payload)
```

But getting json from a sync api view does not work in uvicorn  while working in standard dev server.
```
import httpx


def sync_aggregation(request):
    responses = []
    r = httpx.get("http://127.0.0.1:8000/sync_api_view/")
    responses.append(r.json())
    result = {"responses": responses}
    return JsonResponse(result)
```