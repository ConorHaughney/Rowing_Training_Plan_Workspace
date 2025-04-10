from django.urls import path
from . import views

app_name = 'training_plan_data'

urlpatterns = [
    path('', views.home, name='home'),
    path('training-plan/', views.training_plan, name='training_plan'),
    path('api/training-data/', views.training_data_api, name='training_data_api'),
]