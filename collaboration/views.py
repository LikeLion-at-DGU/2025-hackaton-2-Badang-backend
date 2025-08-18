from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
class 