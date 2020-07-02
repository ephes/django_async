from django.http import HttpResponse


def test_get(request):
    html = "<html><body>Hello World!</body></html>"
    return HttpResponse(html)


async def test_async_get(request):
    html = "<html><body>Hello Async World!</body></html>"
    return HttpResponse(html)
