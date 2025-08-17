from django.shortcuts import render
from rest_framework import viewsets, mixins
from .models import *
from .serializers import *

from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

import re

from .permissions import IsOwnerReadOnly
from rest_framework.decorators import action


# Create your views here.

class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    
    def create(self, request):
        serializer = self.get