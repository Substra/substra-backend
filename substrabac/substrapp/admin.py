from django.contrib import admin

from substrapp.models import Objective, Model, Data, Dataset, Algo

admin.site.register(Objective)
admin.site.register(Model)
admin.site.register(Data)
admin.site.register(Dataset)
admin.site.register(Algo)
