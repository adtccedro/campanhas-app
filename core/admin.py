from django.contrib import admin
from django.utils.formats import number_format

from core.forms import DoacaoFormAdmin

from .models import Campanha, Contribuinte, Contribuinte, Doador, Doacao

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
    
    def get_valor(self, obj):
        return f"R$ {number_format(obj.valor, 2)}"
    get_valor.short_description = 'Valor'
    get_valor.admin_order_field = 'valor'


class ContribuinteAdmin(admin.ModelAdmin):
    list_display = ('doador',)
    search_fields = ('doador__nome', 'campanha__nome')
    list_filter = ('campanha',)


class DoadorAdmin(admin.ModelAdmin):
    search_fields = ('nome', 'email')
    list_display = ('nome', 'email', 'telefone', 'congregacao', 'created_at')


admin.site.register(Campanha, CampanhaAdmin)
admin.site.register(Doador, DoadorAdmin)
admin.site.register(Doacao, DoacaoAdmin)
admin.site.register(Contribuinte, ContribuinteAdmin)