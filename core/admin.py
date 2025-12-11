from django.contrib import admin
from django.utils.formats import number_format

from core.forms import DoacaoFormAdmin

from .models import Campanha, Contribuinte, Doador, Doacao
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum, Count

admin.site.site_header = "Administração Campanhas"
admin.site.site_title = "Administração Campanhas"
admin.site.index_title = "Administração Campanhas"


class CampanhaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_inicio', 'data_fim', 'ativo', 'created_at', 'updated_at')
    search_fields = ('nome',)
    list_filter = ('ativo', 'data_inicio', 'data_fim')


class DoacaoAdmin(admin.ModelAdmin):
    list_display = ('contribuinte', 'get_valor', 'metodo', 'data_doacao', 'mes', 'ano')
    search_fields = ('contribuinte__doador__nome',)
    list_filter = ('metodo', 'data_doacao')
    autocomplete_fields = ('contribuinte', )
    form = DoacaoFormAdmin
    
    def lookup_allowed(self, lookup, value):
        return super().lookup_allowed(lookup, value) or lookup == 'contribuinte__campanha'
    
    def get_valor(self, obj):
        return f"R$ {number_format(obj.valor, 2)}"
    get_valor.short_description = 'Valor'
    get_valor.admin_order_field = 'valor'

    def changelist_view(self, request, extra_context=None):
        """Compute aggregates (sum of `valor` and count) for the changelist queryset
        respecting current filters/search, and pass them to the template via extra_context.
        """
        extra_context = extra_context or {}

        # Use a custom change_list template located in app templates to render totals
        self.change_list_template = 'admin/core/doacao/change_list.html'
        rs = super().changelist_view(request, extra_context=extra_context)
        
        qs = rs.context_data.get('cl').queryset
        # Use the queryset (qs) that already has filters/search applied
        totals = qs.aggregate(total_valor=Sum('valor'), total_count=Count('pk'))
        total_val = totals.get('total_valor') or 0
        total_count = totals.get('total_count') or 0
        # format total_val according to project locale (force grouping for thousands)
        total_val_formatted = f"R$ {number_format(total_val, 2, None, True)}"
        extra_context.update({
            'total_valor': total_val,
            'total_count': total_count,
            'total_valor_formatted': total_val_formatted,
        })
        rs.context_data.update(extra_context)        
        return rs


class ContribuinteAdmin(admin.ModelAdmin):
    list_display = ('doador', 'campanha', 'contribuicoes')
    search_fields = ('doador__nome', 'campanha__nome')
    list_filter = ('campanha',)
    
    def contribuicoes(self, obj):
        url = reverse('admin:core_doacao_changelist') + f'?contribuinte__id__exact={obj.id}'
        return format_html('<a href="{}">Ver contribuições</a>', url)
    contribuicoes.short_description = 'Contribuições'


class DoadorAdmin(admin.ModelAdmin):
    search_fields = ('nome', 'email')
    list_display = ('nome', 'email', 'telefone', 'congregacao', 'created_at')


admin.site.register(Campanha, CampanhaAdmin)
admin.site.register(Doador, DoadorAdmin)
admin.site.register(Doacao, DoacaoAdmin)
admin.site.register(Contribuinte, ContribuinteAdmin)