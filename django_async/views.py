from django.http import HttpResponse


def test_get(request):
    html = "<html><body>Hello World!</body></html>"
    return HttpResponse(html)
