from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('vendas/', include('venda.urls')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),

    # Inclui as rotas de autenticação padrões (login, logout, reset de senha etc.)
    path('accounts/', include('django.contrib.auth.urls')),
]
