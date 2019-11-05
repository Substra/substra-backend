from django.contrib import admin

from substrapp.models import Objective, Model, DataSample, DataManager, Algo

admin.site.register(Algo)
admin.site.register(DataManager)
admin.site.register(DataSample)
admin.site.register(Model)
admin.site.register(Objective)
