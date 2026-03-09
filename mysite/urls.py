from django.contrib import admin
from django.urls import path, include
from mysite import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path("generate_pdf/", views.generate_pdf, name='generate_pdf'),
] 