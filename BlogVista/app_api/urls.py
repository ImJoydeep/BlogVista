from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('blog/', views.BlogPostCreateView.as_view(), name='home'),
    path('search/', views.PostListView.as_view(), name='blog-search'),
    # MIXIN api end-points
    path('create-blog/', views.createBlog.as_view(), name='create-blog'),
    path('list-blog/', views.listBlog.as_view(), name='list-blog'),
    path('retrieve-blog/<int:pk>/', views.retriveBlog.as_view(), name='retrive-blog'),
    path('update-blog/<int:pk>/', views.updateBlog.as_view(), name='update-blog'),
    path('delete-blog/<int:pk>/', views.deleteBlog.as_view(), name='delete-blog'),
    path('search-blog/', views.SearchBlogView.as_view(), name='filter-blog'),
]