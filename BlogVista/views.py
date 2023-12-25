from django.shortcuts import render
from models import Post, Comment
from rest_framework.views import APIView
from models import Post, Comment
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Q
from serializers import PostSerializer
from rest_framework import status


class PublicAPIView(APIView):
    
    def get(self, request):
        try:
            blogs = Post.objects.all().order_by('?')
            if request.GET.get('search'):
                search = request.GET.get('search')
                blogs = blogs.filter(Q(title__icontains = search) | Q(blog_text__icontains = search))
                
            page_number = request.GET.get('page', 1)
            paginator = Paginator(blogs, 1)
            
            serializer = PostSerializer(paginator.page(page_number), many=True)
            response = {
                "results": serializer.data,
                "message": "blog fetched successfully"
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(repr(e), status=status.HTTP_400_BAD_REQUEST)