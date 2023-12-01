# serializers.py
from rest_framework import serializers
from .models import Language, Pages, Content

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class PagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pages
        fields = ('id', 'page_name')
        
class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ('id', 'content', 'language', 'page')


class BlogGetSerializer(serializers.ModelSerializer):
    language_table = LanguageSerializer(source='language', read_only=True)

    class Meta:
        model = Content
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        dynamic_fields = kwargs.pop('dynamic_fields', None)

        super(BlogGetSerializer, self).__init__(*args, **kwargs)

        if dynamic_fields:
            # Dynamically include specified fields from Content model
            allowed_fields = set(dynamic_fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed_fields:
                self.fields.pop(field_name)

            language_fields = LanguageSerializer().fields.keys()
            for field_name in language_fields:
                if field_name in allowed_fields:
                    self.fields[field_name] = serializers.ReadOnlyField(source='language.' + field_name)

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ('id', 'content', 'language', 'page')
