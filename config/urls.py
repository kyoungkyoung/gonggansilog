"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/', permanent=False)),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Custom accounts URLs (우선순위 높음)
    path('auth/', include('allauth.urls')),  # Allauth URLs (소셜 로그인 콜백용)
    path('contracts/', include('contracts.urls')),
    path('records/', include('records.urls')),
    path('recordings/', include('recordings.urls')),
    path('blockchain/', include('blockchain.urls')),
    path('reports/', include('core.reports.urls')),  # Reports engine
    path('exports/', include('core.exports.urls')),  # Export engine
    path('japan/', include('countries.jp.urls')),  # Japan layer
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching
]

# Development only: serve media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
