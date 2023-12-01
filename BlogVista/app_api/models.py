from django.db import models

class Language(models.Model):
    lang_name = models.CharField(max_length=150)
    lang_code = models.CharField(max_length=50, default='en')
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now_add = True)
    
    def __str__(self):
        return self.lang


class Pages(models.Model):
    page_name = models.CharField(max_length = 255)    
    def __str__(self):
        return self.page_name


class Content(models.Model):
    content = models.TextField(max_length=10000)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    page = models.ForeignKey(Pages, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.content


'''
1. language table.
2. page table.
3 content table.

'''