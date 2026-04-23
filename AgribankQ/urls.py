from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('quiz/', include('quiz.urls')),
    path('', RedirectView.as_view(url='/quiz/', permanent=False)),
]
