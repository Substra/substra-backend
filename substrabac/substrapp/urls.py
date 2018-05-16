"""
substrapp URL
"""
from django.urls import re_path
from substrapp import views


urlpatterns = [
    re_path(r'^problem/', views.ProblemList.as_view(), name='problem'),
]
