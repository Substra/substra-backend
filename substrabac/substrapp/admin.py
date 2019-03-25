from django.contrib import admin

from substrapp.models import Objective, Model, Data, DataManager, Algo

admin.site.register(Objective)
admin.site.register(Model)
admin.site.register(Data)
admin.site.register(DataManager)
admin.site.register(Algo)
