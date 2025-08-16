from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action

from .models import *
from .serializers import PostSerializer, PostListSerializer, CommentSerializer, TagSerializer
from .permissions import IsOwnerOrReadOnly

import re

# Create your views here.


class ReviewViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
