from django.urls import path
from .views import (
    VendaListView,
    VendaCreateView,
    VendaUpdateView,
    VendaDeleteView,
    VendaDetailView,
    VendaExportCSVView,
    VendaExportExcelView,
)

app_name = 'venda'

urlpatterns = [
    path('', VendaListView.as_view(), name='listar'),
    path('novo/', VendaCreateView.as_view(), name='criar'),
    path('<int:pk>/editar/', VendaUpdateView.as_view(), name='editar'),
    path('<int:pk>/excluir/', VendaDeleteView.as_view(), name='deletar'),
    path('<int:pk>/', VendaDetailView.as_view(), name='detalhar'),
    path('export/csv/', VendaExportCSVView.as_view(), name='export_csv'),
    path('export/excel/', VendaExportExcelView.as_view(), name='export_excel'),
]
