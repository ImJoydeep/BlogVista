from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework import status
from .models import Language, Pages, Content
from .serializers import BlogGetSerializer, BlogPostSerializer, ContentSerializer


class PostListView(APIView):
    serializer_class = BlogGetSerializer

    def get(self, request, *args, **kwargs):
        # queryset = self.get_queryset()
        lang_id = self.request.query_params.get('lang')
        page_id = self.request.query_params.get('page')

        if lang_id is not None and page_id is not None:
            try:
                language = Language.objects.get(pk=lang_id)
                page = Pages.objects.get(pk=page_id)
            except Language.DoesNotExist:
                return Response(Content.objects.none())
            except Pages.DoesNotExist:
                return Response(Content.objects.none())

            queryset = Content.objects.filter(lang_id=language, page_id=page)
        else:
            queryset = Content.objects.all()
        
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


    # def get(self, *args, **kwargs):
    #     queryset = self.get_queryset()
    #     serializer = self.serializer_class(queryset, many=True)
    #     return Response(serializer.data)


class BlogPostCreateView(generics.CreateAPIView):
    serializer_class = BlogPostSerializer

    def create(self, request, *args, **kwargs):
        print(request.data)
        lang_id = request.data.get('language')
        page_id = request.data.get('page')
        language = None
        page = None
        try:
            language = Language.objects.get(pk=lang_id)
            page = Pages.objects.get(pk=page_id)
        except Language.DoesNotExist:
            return Response({'error': 'Language does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        except Pages.DoesNotExist:
            return Response({'error': 'Page does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return e

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.save(language_id=lang_id, page_id=page_id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# <==============MIXINS===============>

class createBlog(GenericAPIView, CreateModelMixin):
    queryset = Content.objects.all()
    serializer_class = BlogPostSerializer
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
class listBlog(GenericAPIView, ListModelMixin):
    queryset = Content.objects.all()
    serializer_class = BlogGetSerializer
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class retriveBlog(GenericAPIView, RetrieveModelMixin):
    queryset = Content.objects.all()
    serializer_class = BlogGetSerializer
    
    def get(self, request, *args, **kwargs):
        if 'pk' not in kwargs:
            return Response('pk is missing', status=400)
        return self.retrieve(request, *args, **kwargs)

class updateBlog(GenericAPIView, UpdateModelMixin):
    queryset = Content.objects.all()
    serializer_class = BlogPostSerializer
    # Remember to pass pk at the end of EndPoint
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class deleteBlog(GenericAPIView, DestroyModelMixin):
    queryset = Content.objects.all()
    serializer_class = BlogPostSerializer
    # Remember to pass pk at the end of EndPoint
    def post(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class SearchBlogView(ListAPIView):
    serializer_class = BlogGetSerializer

    def get_queryset(self):
        lang_id = self.request.query_params.get('language')
        page_id = self.request.query_params.get('page')
        fields = self.request.query_params.get('fields').split(',')
        print(fields, '======', lang_id, '======', page_id)
        try:
            language = Language.objects.get(pk=lang_id)
            page = Pages.objects.get(pk=page_id)
        except Language.DoesNotExist:
            return Content.objects.none()
        except Pages.DoesNotExist:
            return Content.objects.none()

        queryset = Content.objects.filter(language=language, page=page)
        print("querysetttttttttttttt", queryset)

        return queryset

    def get_serializer(self, *args, **kwargs):
        # Pass the dynamic fields to the serializer
        dynamic_fields = self.request.query_params.get('fields').split(',')
        kwargs['dynamic_fields'] = dynamic_fields
        return super(SearchBlogView, self).get_serializer(*args, **kwargs)