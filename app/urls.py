from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # 👈 importa isso

urlpatterns = [
    path('', RedirectView.as_view(url='/vendas/', permanent=False)),  # 👈 redireciona a raiz
    path('admin/', admin.site.urls),
    path('vendas/', include('venda.urls')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('accounts/', include('django.contrib.auth.urls')),
]
