from django.contrib import admin
from .models import Campanha, Doador, CamanhaDoador, Doacao

admin.site.site_header = "Administração Campanhas"
admin.site.site_title = "Administração Campanhas"
admin.site.index_title = "Administração Campanhas"


class CampanhaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_inicio', 'data_fim', 'ativo', 'created_at', 'updated_at')
    search_fields = ('nome',)
    list_filter = ('ativo', 'data_inicio', 'data_fim')


admin.site.register(Campanha, CampanhaAdmin)
admin.site.register(Doador)
admin.site.register(CamanhaDoador)
admin.site.register(Doacao)