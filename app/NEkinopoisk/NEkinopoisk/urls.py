"""
URL configuration for NEkinopoisk project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from homepage.views import page_not_found

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('homepage.urls')),
    path('search/', include('search.urls')),
    path('movie/', include('movie.urls'))
]

handler404 = page_not_found
