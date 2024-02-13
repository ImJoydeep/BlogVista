"""
party model admin
"""
from django.contrib import admin
from party.models import ContactPurposeType, ContactMethodType, ITUCountry, ISO3166_1Country, ISO3166_2PrimarySubdivisionType, ISO3166_2CountrySubdivision, Language

# Register your models here.
admin.site.register(ContactPurposeType)
admin.site.register(ContactMethodType)
admin.site.register(ITUCountry)
admin.site.register(ISO3166_1Country)
admin.site.register(ISO3166_2PrimarySubdivisionType)
admin.site.register(ISO3166_2CountrySubdivision)
admin.site.register(Language)
