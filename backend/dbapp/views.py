from django.http import JsonResponse
from .models import AppUser

def ping(request):
    return JsonResponse({"message": "pong"})

def users(request):
    data = list(AppUser.objects.values("id", "name", "main_role", "sub_role"))
    return JsonResponse({"users": data})
