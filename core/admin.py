from django.contrib import admin
from django.utils.formats import number_format

from core.forms import DoacaoFormAdmin, DoadorAdminForm

from .models import Campanha, Congregacao, Contribuinte, Doador, Doacao
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum, Count
from dateutil.relativedelta import relativedelta
from django.db.models import F, OuterRef, Subquery, Count, Q, IntegerField, Value, Case, When
from django.db.models.functions import ExtractYear, ExtractMonth

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
    list_filter = ('metodo', 'data_doacao', 'contribuinte__doador__congregacao_fk', 'contribuinte__campanha', 'prestado_contas')
    autocomplete_fields = ('contribuinte', )
    form = DoacaoFormAdmin
    actions = ['mark_as_prestado_contas']
    
    def mark_as_prestado_contas(self, request, queryset):
        updated_count = queryset.update(prestado_contas=True)
        self.message_user(request, f"{updated_count} doações marcadas como 'Prestado Contas'.")
    mark_as_prestado_contas.short_description = "Marcar doações selecionadas como 'Prestado Contas'"
    
    
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


class StatusListFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('pendente', 'Pendente'),
            ('parcial', 'Parcial'),
            ('completo', 'Completo'),
            ('indefinido', 'Indefinido'),
        ]

    def queryset(self, request, queryset):

        # Annotate each Contribuinte with meses_contribuidos and total_months
        qs = queryset.annotate(
            data_inicio=F('campanha__data_inicio'),
            data_fim=F('campanha__data_fim'),
        ).annotate(
            total_months=Case(
                When(
                    Q(data_inicio__isnull=False) & Q(data_fim__isnull=False),
                    then=(
                    (ExtractYear('data_fim') - ExtractYear('data_inicio')) * 12 +
                    (ExtractMonth('data_fim') - ExtractMonth('data_inicio')) + 1
                    )
                ),
                default=Value(0),
                output_field=IntegerField()
            ),
            meses_contribuidos=Subquery(
                Doacao.objects.filter(
                    contribuinte_id=OuterRef('pk')
                ).values('contribuinte_id')
                .annotate(
                    count=Count('mes', distinct=True)
                ).values('count'),
                output_field=IntegerField()
            )
        )

        value = self.value()
        if value == 'indefinido':
            return qs.filter(Q(data_inicio__isnull=True) | Q(data_fim__isnull=True))
        if value == 'pendente':
            return qs.filter(
                Q(data_inicio__isnull=False) & Q(data_fim__isnull=False),
                Q(doacoes__isnull=True) | Q(meses_contribuidos=0)
            )
        if value == 'completo':
            return qs.filter(
                Q(data_inicio__isnull=False) & Q(data_fim__isnull=False),
                meses_contribuidos__gte=F('total_months')
            )
        if value == 'parcial':
            return qs.filter(
                Q(data_inicio__isnull=False) & Q(data_fim__isnull=False),
                meses_contribuidos__gt=0,
                meses_contribuidos__lt=F('total_months')
            )
        return qs
    
class ContribuinteAdmin(admin.ModelAdmin):
    list_display = ('doador', 'status', 'contribuicoes', 'campanha',)
    search_fields = ('doador__nome', 'campanha__nome')
    list_filter = ('campanha', StatusListFilter, 'doador__congregacao_fk',)
    autocomplete_fields = ('doador', 'campanha')
    
    def contribuicoes(self, obj):
        url = reverse('admin:core_doacao_changelist') + f'?contribuinte__id__exact={obj.id}'
        return format_html('<a href="{}">Ver contribuições</a>', url)
    contribuicoes.short_description = 'Contribuições'
    

        
    def status(self, obj):
        campanha = obj.campanha
        if not campanha.data_inicio or not campanha.data_fim:
            return "Indefinido"
        # Calcula o total de meses da campanha
        total_months = (campanha.data_fim.year - campanha.data_inicio.year) * 12 + (campanha.data_fim.month - campanha.data_inicio.month) + 1

        # Conta quantos meses o contribuinte já contribuiu (considerando doações únicas por mês)
        meses_contribuidos = obj.doacoes.values('ano', 'mes').distinct().count()

        # Determina status
        if meses_contribuidos == 0:
            status = "Pendente"
        elif meses_contribuidos >= total_months:
            status = "Completo"
        else:
            status = "Parcial"

        return f"{status} ({meses_contribuidos}/{total_months})"
    status.short_description = 'Status'


class DoadorAdmin(admin.ModelAdmin):
    search_fields = ('nome', 'email')
    list_display = ('nome', 'email', 'telefone', 'congregacao_fk', 'created_at')
    exclude = ('congregacao',)
    form = DoadorAdminForm

class CongregacaoAdmin(admin.ModelAdmin):
    search_fields = ('nome',)        


admin.site.register(Campanha, CampanhaAdmin)
admin.site.register(Doador, DoadorAdmin)
admin.site.register(Doacao, DoacaoAdmin)
admin.site.register(Contribuinte, ContribuinteAdmin)
admin.site.register(Congregacao, CongregacaoAdmin)
