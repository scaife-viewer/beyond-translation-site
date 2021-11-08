from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .utils import proxy_query


@csrf_exempt
def proxy_view(request):
    data = proxy_query(request)
    return JsonResponse(data=data)
