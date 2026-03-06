from django.contrib import admin
from django.urls import path, include

from area.views import webhook_kiwify

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/webhooks/kiwify/', webhook_kiwify, name='webhook_kiwify'),
    path('', include('user.urls')),
    path('dashboard/', include('area.urls'))
]
