from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponse
from datetime import datetime
from io import BytesIO
import csv
from openpyxl import Workbook

from .models import Venda
from .forms import VendaForm

class VendaListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = Venda
    template_name = 'venda/venda_list.html'
    context_object_name = 'vendas'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        data = self.request.GET.get('data')

        if data:
            data = data.replace(" até ", " to ")
            if " to " in data:
                data_inicio, data_fim = data.split(" to ")
                data_inicio = datetime.strptime(data_inicio.strip(), "%d/%m/%Y").date()
                data_fim = datetime.strptime(data_fim.strip(), "%d/%m/%Y").date()
                queryset = queryset.filter(data__range=[data_inicio, data_fim])
            else:
                data_unica = datetime.strptime(data.strip(), "%d/%m/%Y").date()
                queryset = queryset.filter(data=data_unica)

        return queryset.order_by('-data')


class VendaCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = Venda
    form_class = VendaForm
    template_name = 'venda/venda_form.html'
    success_url = reverse_lazy('venda:listar')

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)


class VendaUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = Venda
    form_class = VendaForm
    template_name = 'venda/venda_form.html'
    success_url = reverse_lazy('venda:listar')

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)


class VendaDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = Venda
    template_name = 'venda/venda_confirm_delete.html'
    success_url = reverse_lazy('venda:listar')


class VendaDetailView(LoginRequiredMixin, DetailView):
    login_url = '/accounts/login/'
    model = Venda
    template_name = 'venda/venda_detail.html'
    context_object_name = 'venda'


# Exportação em CSV utilizando class-based view – herda os filtros da listagem
class VendaExportCSVView(VendaListView):
    def render_to_response(self, context, **response_kwargs):
        vendas = self.get_queryset()
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="vendas.csv"'},
        )
        writer = csv.writer(response)
        # Cabeçalho conforme exibido na tabela
        writer.writerow([
            "Data", "Mês", "Ano", "Semana",
            "Invest. Realizado", "Invest. Projetado", "Saldo Invest.",
            "Vendas Google/Meta", "FAT Projetado", "FAT Campanha", "FAT Geral", "Saldo FAT",
            "ROI", "ROAS", "CAC", "TKT Médio", "ARPU",
            "Leads", "Novos", "Recorrentes", "Conversões", "Taxa Conv.", "Clima"
        ])

        for venda in vendas:
            writer.writerow([
                venda.data.strftime("%d/%m/%Y") if venda.data else "",
                venda.mes,
                venda.ano,
                venda.semana,
                venda.invest_realizado,
                venda.invest_projetado,
                venda.saldo_invest,
                venda.vendas_google_meta,
                venda.fat_proj,
                venda.fat_camp_realizado,
                venda.fat_geral,
                venda.saldo_fat,
                venda.roi_realizado,
                venda.roas_realizado,
                venda.cac_realizado,
                venda.ticket_medio_realizado,
                venda.arpu_realizado,
                venda.leads,
                venda.clientes_novos,
                venda.clientes_recorrentes,
                venda.conversoes,
                venda.taxa_conversao,
                venda.clima,
            ])

        return response


# Exportação em Excel (XLSX) utilizando class-based view – reaproveitando os filtros da listagem
class VendaExportExcelView(VendaListView):
    def render_to_response(self, context, **response_kwargs):
        vendas = self.get_queryset()
        workbook = Workbook()
        sheet = workbook.active

        header = [
            "Data", "Mês", "Ano", "Semana",
            "Invest. Realizado", "Invest. Projetado", "Saldo Invest.",
            "Vendas Google/Meta", "FAT Projetado", "FAT Campanha", "FAT Geral", "Saldo FAT",
            "ROI", "ROAS", "CAC", "TKT Médio", "ARPU",
            "Leads", "Novos", "Recorrentes", "Conversões", "Taxa Conv.", "Clima"
        ]
        sheet.append(header)

        for venda in vendas:
            row = [
                venda.data.strftime("%d/%m/%Y") if venda.data else "",
                venda.mes,
                venda.ano,
                venda.semana,
                venda.invest_realizado,
                venda.invest_projetado,
                venda.saldo_invest,
                venda.vendas_google_meta,
                venda.fat_proj,
                venda.fat_camp_realizado,
                venda.fat_geral,
                venda.saldo_fat,
                venda.roi_realizado,
                venda.roas_realizado,
                venda.cac_realizado,
                venda.ticket_medio_realizado,
                venda.arpu_realizado,
                venda.leads,
                venda.clientes_novos,
                venda.clientes_recorrentes,
                venda.conversoes,
                venda.taxa_conversao,
                venda.clima,
            ]
            sheet.append(row)

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="vendas.xlsx"'
        return response
