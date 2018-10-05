from django.contrib import admin

from substrapp.models import Challenge, Model, Data, Dataset, Algo

admin.site.register(Challenge)
admin.site.register(Model)
admin.site.register(Data)
admin.site.register(Dataset)
admin.site.register(Algo)
