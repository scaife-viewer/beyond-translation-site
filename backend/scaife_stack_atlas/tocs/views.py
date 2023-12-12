import os

from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse, Http404, JsonResponse
from django.urls import reverse


TOC_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "tocs")
CACHE_FOREVER = None


def tocs_index(request):
    key = "tocs-index"
    data = cache.get(key)
    if data is None:
        data = []
        files = [f for f in os.listdir(TOC_DATA_PATH) if f.count(".json")]
        for filename in files:
            data.append(reverse("serve_toc", args=[filename]))
        cache.set(key, data, CACHE_FOREVER)
    return JsonResponse({"tocs": data})


def serve_toc(request, filename):
    path = os.path.join(TOC_DATA_PATH, filename)
    if not os.path.exists(path):
        raise Http404
    return FileResponse(open(path, "rb"))
