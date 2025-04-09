"""
Views do Dashboard de Desempenho.

Dependendo do filtro escolhido pelo usuário (via parâmetro GET 'filter'),
- Se for 'semana': os dados são filtrados por ano, mês e semana, e os cards exibem o faturamento da semana (com delta).
- Se for 'mes': os dados são filtrados por ano e mês e os cards exibem o faturamento geral do mês.
- Se for 'ano': os dados são filtrados somente por ano e os cards exibem o faturamento geral do ano.

Os gráficos sempre exibem os dados completos do período (para 'mes' ou 'semana' agrupados por semana e para 'ano' agrupados por mês).
"""

from django.views.generic import TemplateView
from venda.models import Venda
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime
import calendar
import json

class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = '/accounts/login/'

    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = datetime.now()

        # Lista de meses para exibição
        months = [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ]

        # Tipos de filtro disponíveis
        filter_types = [
            ('ano', 'Ano Todo'),
            ('mes', 'Mês'),
            ('semana', 'Semana')
        ]

        # Parâmetros GET
        year_selected = int(self.request.GET.get('year', now.year))
        month_selected = int(self.request.GET.get('month', now.month))
        week_selected = self.request.GET.get('week', str(now.isocalendar()[1]))
        filter_type = self.request.GET.get('filter', 'semana')  # padrão: 'semana'

        # Para 'mes' e 'semana', calcula as semanas disponíveis para o mês
        if filter_type in ['mes', 'semana']:
            _, last_day = calendar.monthrange(year_selected, month_selected)
            days_in_month = [datetime(year_selected, month_selected, d) for d in range(1, last_day + 1)]
            available_weeks = sorted(set(day.isocalendar()[1] for day in days_in_month))
        else:
            available_weeks = []

        # Funções auxiliares
        def safe_sum(values):
            return sum(v for v in values if v is not None)

        def safe_mean(values):
            vals = [v for v in values if v is not None]
            return sum(vals)/len(vals) if vals else 0

        def overall_average(data):
            return sum(data)/len(data) if data else 0

        # ========= Filtragem =========
        if filter_type == 'ano':
            queryset_full = Venda.objects.filter(data__year=year_selected)
        else:
            queryset_full = Venda.objects.filter(data__year=year_selected, data__month=month_selected)

        # Para os cards:
        if filter_type == 'semana':
            queryset_cards = queryset_full.filter(data__week=week_selected) if week_selected else queryset_full
        else:
            queryset_cards = queryset_full

        # ========= Dados para os GRÁFICOS =========
        if filter_type == 'ano':
            # Agrupa por mês
            chart_queryset = queryset_full
            group_data = {}
            for venda in chart_queryset:
                m = venda.data.month
                group_data.setdefault(m, []).append(venda)
            sorted_keys_chart = sorted(group_data.keys())
            chart_labels = [next((name for num, name in months if num == m), str(m)) for m in sorted_keys_chart]
            invest_realizado_sum   = [safe_sum([float(e.invest_realizado) for e in group_data[m]]) for m in sorted_keys_chart]
            invest_projetado_sum   = [safe_sum([float(e.invest_projetado) for e in group_data[m]]) for m in sorted_keys_chart]
            saldo_invest_sum       = [safe_sum([float(e.saldo_invest) for e in group_data[m] if e.saldo_invest is not None]) for m in sorted_keys_chart]
            fat_camp_realizado_sum = [safe_sum([float(e.fat_camp_realizado) for e in group_data[m]]) for m in sorted_keys_chart]
            fat_geral_sum          = [safe_sum([float(e.fat_geral) for e in group_data[m]]) for m in sorted_keys_chart]
            saldo_fat_sum          = [safe_sum([float(e.saldo_fat) for e in group_data[m] if e.saldo_fat is not None]) for m in sorted_keys_chart]
            leads_sum              = [safe_sum([e.leads for e in group_data[m]]) for m in sorted_keys_chart]
            clientes_novos_sum     = [safe_sum([e.clientes_novos for e in group_data[m]]) for m in sorted_keys_chart]
            clientes_recorrentes_sum = [safe_sum([e.clientes_recorrentes for e in group_data[m]]) for m in sorted_keys_chart]
            vendas_google_meta_sum = [safe_sum([float(e.vendas_google_meta) for e in group_data[m]]) for m in sorted_keys_chart]
            taxa_conversao_avg     = [safe_mean([float(e.taxa_conversao) for e in group_data[m] if e.taxa_conversao is not None]) for m in sorted_keys_chart]
            roi_avg                = [safe_mean([float(e.roi_realizado) for e in group_data[m] if e.roi_realizado is not None]) for m in sorted_keys_chart]
            ticket_medio_avg       = [safe_mean([float(e.ticket_medio_realizado) for e in group_data[m] if e.ticket_medio_realizado is not None]) for m in sorted_keys_chart]
            cac_avg                = [safe_mean([float(e.cac_realizado) for e in group_data[m] if e.cac_realizado is not None]) for m in sorted_keys_chart]
        else:
            # Para "mes" e "semana", agrupamos por semana
            chart_queryset = queryset_full
            weekly_data = {}
            for venda in chart_queryset:
                w = venda.data.isocalendar()[1]
                weekly_data.setdefault(w, []).append(venda)
            sorted_keys_chart = sorted(weekly_data.keys())
            chart_labels = [f"Semana {w}" for w in sorted_keys_chart]
            invest_realizado_sum   = [safe_sum([float(e.invest_realizado) for e in weekly_data[w]]) for w in sorted_keys_chart]
            invest_projetado_sum   = [safe_sum([float(e.invest_projetado) for e in weekly_data[w]]) for w in sorted_keys_chart]
            saldo_invest_sum       = [safe_sum([float(e.saldo_invest) for e in weekly_data[w] if e.saldo_invest is not None]) for w in sorted_keys_chart]
            fat_camp_realizado_sum = [safe_sum([float(e.fat_camp_realizado) for e in weekly_data[w]]) for w in sorted_keys_chart]
            fat_geral_sum          = [safe_sum([float(e.fat_geral) for e in weekly_data[w]]) for w in sorted_keys_chart]
            saldo_fat_sum          = [safe_sum([float(e.saldo_fat) for e in weekly_data[w] if e.saldo_fat is not None]) for w in sorted_keys_chart]
            leads_sum              = [safe_sum([e.leads for e in weekly_data[w]]) for w in sorted_keys_chart]
            clientes_novos_sum     = [safe_sum([e.clientes_novos for e in weekly_data[w]]) for w in sorted_keys_chart]
            clientes_recorrentes_sum = [safe_sum([e.clientes_recorrentes for e in weekly_data[w]]) for w in sorted_keys_chart]
            vendas_google_meta_sum = [safe_sum([float(e.vendas_google_meta) for e in weekly_data[w]]) for w in sorted_keys_chart]
            taxa_conversao_avg     = [safe_mean([float(e.taxa_conversao) for e in weekly_data[w] if e.taxa_conversao is not None]) for w in sorted_keys_chart]
            roi_avg                = [safe_mean([float(e.roi_realizado) for e in weekly_data[w] if e.roi_realizado is not None]) for w in sorted_keys_chart]
            ticket_medio_avg       = [safe_mean([float(e.ticket_medio_realizado) for e in weekly_data[w] if e.ticket_medio_realizado is not None]) for w in sorted_keys_chart]
            cac_avg                = [safe_mean([float(e.cac_realizado) for e in weekly_data[w] if e.cac_realizado is not None]) for w in sorted_keys_chart]

        # ========= Dados para os CARDS =========
        # Os cards utilizam o conjunto queryset_cards, filtrado apenas quando for "semana"
        card_faturamento_value         = safe_sum([float(getattr(e, 'fat_geral')) for e in queryset_cards])
        card_clientes_novos_value      = safe_sum([getattr(e, 'clientes_novos') for e in queryset_cards])
        card_fatcamp_value             = safe_sum([float(getattr(e, 'fat_camp_realizado')) for e in queryset_cards])
        card_leads_value               = safe_sum([getattr(e, 'leads') for e in queryset_cards])
        card_vendas_google_value       = safe_sum([float(getattr(e, 'vendas_google_meta')) for e in queryset_cards])
        card_roi_value                 = safe_sum([float(getattr(e, 'roi_realizado')) for e in queryset_cards])
        card_ticket_value              = safe_sum([float(getattr(e, 'ticket_medio_realizado')) for e in queryset_cards])
        card_clientes_recorrentes_value = safe_sum([getattr(e, 'clientes_recorrentes') for e in queryset_cards])
        card_taxa_value                = safe_sum([float(getattr(e, 'taxa_conversao')) for e in queryset_cards])
        card_cac_value                 = safe_sum([float(getattr(e, 'cac_realizado')) for e in queryset_cards])

        # Calcula as médias globais do período para os cards (usando queryset_full agrupado)
        if filter_type in ['mes', 'semana']:
            data_group = {}
            for venda in queryset_full:
                w = venda.data.isocalendar()[1]
                data_group.setdefault(w, []).append(venda)
            sorted_keys_card = sorted(data_group.keys())
            fat_geral_full         = [safe_sum([float(e.fat_geral) for e in data_group[w]]) for w in sorted_keys_card]
            fat_camp_full          = [safe_sum([float(e.fat_camp_realizado) for e in data_group[w]]) for w in sorted_keys_card]
            clientes_novos_full      = [safe_sum([e.clientes_novos for e in data_group[w]]) for w in sorted_keys_card]
            leads_full             = [safe_sum([e.leads for e in data_group[w]]) for w in sorted_keys_card]
            vendas_google_full     = [safe_sum([float(e.vendas_google_meta) for e in data_group[w]]) for w in sorted_keys_card]
            clientes_recorrentes_full = [safe_sum([e.clientes_recorrentes for e in data_group[w]]) for w in sorted_keys_card]
            taxa_full              = [safe_mean([float(e.taxa_conversao) for e in data_group[w] if e.taxa_conversao is not None]) for w in sorted_keys_card]
            roi_full               = [safe_mean([float(e.roi_realizado) for e in data_group[w] if e.roi_realizado is not None]) for w in sorted_keys_card]
            ticket_medio_full      = [safe_mean([float(e.ticket_medio_realizado) for e in data_group[w] if e.ticket_medio_realizado is not None]) for w in sorted_keys_card]
            cac_full               = [safe_mean([float(e.cac_realizado) for e in data_group[w] if e.cac_realizado is not None]) for w in sorted_keys_card]
        else:  # filter_type == 'ano'
            data_group = {}
            for venda in queryset_full:
                m = venda.data.month
                data_group.setdefault(m, []).append(venda)
            sorted_keys_card = sorted(data_group.keys())
            fat_geral_full         = [safe_sum([float(e.fat_geral) for e in data_group[m]]) for m in sorted_keys_card]
            fat_camp_full          = [safe_sum([float(e.fat_camp_realizado) for e in data_group[m]]) for m in sorted_keys_card]
            clientes_novos_full      = [safe_sum([e.clientes_novos for e in data_group[m]]) for m in sorted_keys_card]
            leads_full             = [safe_sum([e.leads for e in data_group[m]]) for m in sorted_keys_card]
            vendas_google_full     = [safe_sum([float(e.vendas_google_meta) for e in data_group[m]]) for m in sorted_keys_card]
            clientes_recorrentes_full = [safe_sum([e.clientes_recorrentes for e in data_group[m]]) for m in sorted_keys_card]
            taxa_full              = [safe_mean([float(e.taxa_conversao) for e in data_group[m] if e.taxa_conversao is not None]) for m in sorted_keys_card]
            roi_full               = [safe_mean([float(e.roi_realizado) for e in data_group[m] if e.roi_realizado is not None]) for m in sorted_keys_card]
            ticket_medio_full      = [safe_mean([float(e.ticket_medio_realizado) for e in data_group[m] if e.ticket_medio_realizado is not None]) for m in sorted_keys_card]
            cac_full               = [safe_mean([float(e.cac_realizado) for e in data_group[m] if e.cac_realizado is not None]) for m in sorted_keys_card]

        avg_faturamento         = overall_average(fat_geral_full)
        avg_clientes_novos      = overall_average(clientes_novos_full)
        avg_fatcamp             = overall_average(fat_camp_full)
        avg_leads               = overall_average(leads_full)
        avg_vendas_google       = overall_average(vendas_google_full)
        avg_roi                 = overall_average(roi_full)
        avg_ticket              = overall_average(ticket_medio_full)
        avg_clientes_recorrentes = overall_average(clientes_recorrentes_full)
        avg_taxa                = overall_average(taxa_full)
        avg_cac                 = overall_average(cac_full)

        diff_faturamento       = card_faturamento_value - avg_faturamento
        diff_clientes_novos    = card_clientes_novos_value - avg_clientes_novos
        diff_fatcamp           = card_fatcamp_value - avg_fatcamp
        diff_leads             = card_leads_value - avg_leads
        diff_vendas_google     = card_vendas_google_value - avg_vendas_google
        diff_roi               = card_roi_value - avg_roi
        diff_ticket            = card_ticket_value - avg_ticket
        diff_clientes_recorrentes = card_clientes_recorrentes_value - avg_clientes_recorrentes
        diff_taxa              = card_taxa_value - avg_taxa
        diff_cac               = card_cac_value - avg_cac

        def diff_message(diff):
            if diff < 0:
                return f"Abaixo da média em R$ {abs(diff):,.2f}"
            elif diff > 0:
                return f"Acima da média em R$ {diff:,.2f}"
            else:
                return "Na média"

        faturamento_geral_mes = safe_sum([float(e.fat_geral) for e in queryset_full])
        queryset_year = Venda.objects.filter(data__year=year_selected)
        faturamento_geral_ano = safe_sum([float(e.fat_geral) for e in queryset_year])

        # ========= Definição dos GRÁFICOS =========
        charts = {
            'chartInvestimento': {
                'title': 'Análise de Investimento',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'Invest. Realizado (R$)',
                            'data': invest_realizado_sum,
                            'borderColor': 'rgba(75, 192, 192, 1)',
                            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Invest. Projetado (R$)',
                            'data': invest_projetado_sum,
                            'borderColor': 'rgba(255, 99, 132, 1)',
                            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Saldo Invest.',
                            'data': saldo_invest_sum,
                            'type': 'line'
                        }
                    ]
                })
            },
            'chartFaturamento': {
                'title': 'Análise de Faturamento',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'Fat. Camp. (R$)',
                            'data': fat_camp_realizado_sum,
                            'borderColor': 'rgba(54, 162, 235, 1)',
                            'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Fat. Geral (R$)',
                            'data': fat_geral_sum,
                            'borderColor': 'rgba(75, 192, 192, 1)',
                            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Saldo FAT',
                            'data': saldo_fat_sum,
                            'type': 'line'
                        }
                    ]
                })
            },
            'chartROI': {
                'title': 'Análise de ROI',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'ROI Realizado',
                            'data': roi_avg,
                            'borderColor': 'rgba(148, 0, 211, 1)',
                            'backgroundColor': 'rgba(148, 0, 211, 0.3)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Média ROI',
                            'data': [overall_average(roi_avg)] * len(chart_labels),
                            'type': 'line',
                            'borderColor': 'rgba(173, 216, 230, 1)',
                            'borderDash': [5, 5]
                        }
                    ]
                })
            },
            'chartLeads': {
                'title': 'Análise de LEADS',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'LEADS',
                            'data': leads_sum,
                            'borderColor': 'rgba(153, 102, 255, 1)',
                            'backgroundColor': 'rgba(153, 102, 255, 0.3)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Média LEADS',
                            'data': [overall_average(leads_sum)] * len(chart_labels),
                            'type': 'line',
                            'borderColor': 'rgba(173, 216, 230, 1)',
                            'borderDash': [5, 5]
                        }
                    ]
                })
            },
            'chartTicketMedio': {
                'title': 'Análise de Ticket Médio',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'Ticket Médio (R$)',
                            'data': ticket_medio_avg,
                            'borderColor': 'rgba(255, 159, 64, 1)',
                            'backgroundColor': 'rgba(255, 159, 64, 0.3)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Média Ticket Médio',
                            'data': [overall_average(ticket_medio_avg)] * len(chart_labels),
                            'type': 'line',
                            'borderColor': 'rgba(173, 216, 230, 1)',
                            'borderDash': [5, 5]
                        }
                    ]
                })
            },
            'chartClientesNovos': {
                'title': 'Análise de Clientes Novos',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'Clientes Novos',
                            'data': clientes_novos_sum,
                            'borderColor': 'rgba(255, 99, 132, 1)',
                            'backgroundColor': 'rgba(255, 99, 132, 0.3)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Média Clientes Novos',
                            'data': [overall_average(clientes_novos_sum)] * len(chart_labels),
                            'type': 'line',
                            'borderColor': 'rgba(173, 216, 230, 1)',
                            'borderDash': [5, 5]
                        }
                    ]
                })
            },
            'chartClientesRecorrentes': {
                'title': 'Análise de Clientes Recorrentes',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'Clientes Recorrentes',
                            'data': clientes_recorrentes_sum,
                            'borderColor': 'rgba(54, 162, 235, 1)',
                            'backgroundColor': 'rgba(54, 162, 235, 0.3)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Média Clientes Recorrentes',
                            'data': [overall_average(clientes_recorrentes_sum)] * len(chart_labels),
                            'type': 'line',
                            'borderColor': 'rgba(173, 216, 230, 1)',
                            'borderDash': [5, 5]
                        }
                    ]
                })
            },
            'chartVendasGoogle': {
                'title': 'Análise de Vendas Goog./Meta',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'Vendas Goog./Meta (R$)',
                            'data': vendas_google_meta_sum,
                            'borderColor': 'rgba(201, 203, 207, 1)',
                            'backgroundColor': 'rgba(201, 203, 207, 0.3)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Média Vendas Goog./Meta',
                            'data': [overall_average(vendas_google_meta_sum)] * len(chart_labels),
                            'type': 'line',
                            'borderColor': 'rgba(173, 216, 230, 1)',
                            'borderDash': [5, 5]
                        }
                    ]
                })
            },
            'chartTaxaConversao': {
                'title': 'Análise de Taxa de Conversão',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'Taxa de Conversão',
                            'data': taxa_conversao_avg,
                            'borderColor': 'rgba(255, 205, 86, 1)',
                            'backgroundColor': 'rgba(255, 205, 86, 0.3)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Média Taxa de Conversão',
                            'data': [overall_average(taxa_conversao_avg)] * len(chart_labels),
                            'type': 'line',
                            'borderColor': 'rgba(173, 216, 230, 1)',
                            'borderDash': [5, 5]
                        }
                    ]
                })
            },
            'chartCAC': {
                'title': 'Análise de CAC',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'CAC Realizado (R$)',
                            'data': cac_avg,
                            'borderColor': 'rgba(255, 159, 64, 1)',
                            'backgroundColor': 'rgba(255, 159, 64, 0.3)',
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        },
                        {
                            'label': 'Média CAC',
                            'data': [overall_average(cac_avg)] * len(chart_labels),
                            'type': 'line',
                            'borderColor': 'rgba(173, 216, 230, 1)',
                            'borderDash': [5, 5]
                        }
                    ]
                })
            },
            'chartTKT_vs_CAC': {
                'title': 'Ticket Médio vs CAC',
                'data': json.dumps({
                    'labels': chart_labels,
                    'datasets': [
                        {
                            'label': 'CAC Realizado (R$)',
                            'data': cac_avg,
                            'borderColor': 'rgba(54, 162, 235, 1)',
                            'backgroundColor': 'rgba(54, 162, 235, 0.3)',
                            'fill': True
                        },
                        {
                            'label': 'Ticket Médio (R$)',
                            'data': ticket_medio_avg,
                            'borderColor': 'rgba(75, 192, 192, 1)',
                            'backgroundColor': 'rgba(75, 192, 192, 0.3)',
                            'fill': True
                        },
                        {
                            'label': 'Diferença (Ticket - CAC)',
                            'data': [tm - cac for tm, cac in zip(ticket_medio_avg, cac_avg)],
                            'type': 'line'
                        }
                    ]
                })
            }
        }

        # ========= Definição dos CARDS =========
        # Para o card de Faturamento, se o filtro for 'mes' ou 'ano'
        # usamos os valores agregados de todo o período (mês ou ano), sem delta.
        if filter_type == 'semana':
            card_faturamento = {
                'class': 'bg-primary',
                'icon': 'fas fa-dollar-sign',
                'title': 'Faturamento semana',
                'value': f'R$ {card_faturamento_value:,.2f}',
                'diff': diff_message(diff_faturamento)
            }
        elif filter_type == 'mes':
            card_faturamento = {
                'class': 'bg-secondary',
                'icon': 'fas fa-calendar-alt',
                'title': 'Faturamento Geral do Mês',
                'value': f'R$ {faturamento_geral_mes:,.2f}',
                'diff': ''
            }
        else:  # filter_type == 'ano'
            card_faturamento = {
                'class': 'bg-dark',
                'icon': 'fas fa-calendar',
                'title': 'Faturamento Geral do Ano',
                'value': f'R$ {faturamento_geral_ano:,.2f}',
                'diff': ''
            }

        # Outros cards permanecem inalterados
        cards = {
            'cardFaturamento': card_faturamento,
            'cardClientesNovos': {
                'class': 'bg-info',
                'icon': 'fas fa-user-plus',
                'title': 'Clientes Novos semana',
                'value': f'{card_clientes_novos_value}',
                'diff': diff_message(diff_clientes_novos)
            },
            'cardFatCamp': {
                'class': 'bg-warning',
                'icon': 'fas fa-chart-line',
                'title': 'Fatur. Camp. semana',
                'value': f'R$ {card_fatcamp_value:,.2f}',
                'diff': diff_message(diff_fatcamp)
            },
            'cardLead': {
                'class': 'bg-secondary',
                'icon': 'fas fa-bullhorn',
                'title': 'LEAD semana',
                'value': f'{card_leads_value}',
                'diff': diff_message(diff_leads)
            },
            'cardVendasGoogle': {
                'class': 'bg-danger',
                'icon': 'fas fa-ad',
                'title': 'Vendas Goog./Meta semana',
                'value': f'R$ {card_vendas_google_value:,.2f}',
                'diff': diff_message(diff_vendas_google)
            },
            'cardROI': {
                'class': 'bg-dark',
                'icon': 'fas fa-percentage',
                'title': 'ROI semana',
                'value': f'{card_roi_value:.2f}',
                'diff': diff_message(diff_roi)
            },
            'cardTicketMedio': {
                'class': 'bg-success',
                'icon': 'fas fa-hand-holding-usd',
                'title': 'TKT. Med. semana',
                'value': f'R$ {card_ticket_value:,.2f}',
                'diff': diff_message(diff_ticket)
            },
            'cardClientesRecorrentes': {
                'class': 'bg-primary',
                'icon': 'fas fa-users',
                'title': 'Clientes Recor. semana',
                'value': f'{card_clientes_recorrentes_value}',
                'diff': diff_message(diff_clientes_recorrentes)
            },
            'cardTaxaConversao': {
                'class': 'bg-info',
                'icon': 'fas fa-signal',
                'title': 'Taxa de conver. semana',
                'value': f'{card_taxa_value:.3f}',
                'diff': diff_message(diff_taxa)
            },
            'cardCAC': {
                'class': 'bg-warning',
                'icon': 'fas fa-calculator',
                'title': 'CAC semana',
                'value': f'R$ {card_cac_value:,.2f}',
                'diff': diff_message(diff_cac)
            },
            'cardFaturamentoMes': {
                'class': 'bg-secondary',
                'icon': 'fas fa-calendar-alt',
                'title': 'Faturamento Geral do Mês',
                'value': f'R$ {faturamento_geral_mes:,.2f}',
                'diff': ''
            },
            'cardFaturamentoAno': {
                'class': 'bg-dark',
                'icon': 'fas fa-calendar',
                'title': 'Faturamento Geral do Ano',
                'value': f'R$ {faturamento_geral_ano:,.2f}',
                'diff': ''
            }
        }

        context.update({
            'years': sorted({v.data.year for v in Venda.objects.all()}),
            'months': months,
            'year_selected': year_selected,
            'month_selected': month_selected,
            'week_selected': week_selected,
            'filter_type': filter_type,
            'filter_types': filter_types,
            'available_weeks': available_weeks,
            'charts': charts,
            'cards': cards
        })

        return context
