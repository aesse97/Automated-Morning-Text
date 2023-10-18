from django.urls import path
from . import views

urlpatterns = [
    path('sms/', views.sms_reply, name='sms_reply'),
]