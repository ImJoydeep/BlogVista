from django.shortcuts import render
from app.models import Post, Comment
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Q
from app.serializers import PostSerializer
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework import status


class PublicAPIView(APIView):
    
    def get(self, request):
        try:
            blogs = Post.objects.all().order_by('?')
            if request.GET.get('search'):
                search = request.GET.get('search')
                blogs1 = Post.objects.filter(Q(title__icontains = search))
                blogs2 = Post.objects.filter(Q(content__icontains = search))
                blogs = blogs1.union(blogs2)
                page_number = request.GET.get('page', 1)
                paginator = Paginator(blogs, 10)
            
                serializer = PostSerializer(paginator.page(page_number), many=True)
                response = {
                "results": serializer.data,
                "message": "blog successfully"
                }
                return Response(response, status=status.HTTP_200_OK)
                
            page_number = request.GET.get('page', 1)
            paginator = Paginator(blogs, 10)
            
            serializer = PostSerializer(paginator.page(page_number), many=True)
            response = {
                "results": serializer.data,
                "message": "blog fetched successfully"
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(repr(e), status=status.HTTP_400_BAD_REQUEST)
        
class createBlog(GenericAPIView, CreateModelMixin):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
