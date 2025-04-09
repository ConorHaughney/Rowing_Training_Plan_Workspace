from django.urls import path
from . import views

app_name = 'training_plan_data'

urlpatterns = [
    path('', views.home, name='home'),
]