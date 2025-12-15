from django import forms

from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib import admin
from core.models import Contribuinte, Doacao, Doador, Campanha
from datetime import date
from decimal import Decimal


class DoadorAdminForm(forms.ModelForm):
    congregacao_fk = forms.ModelChoiceField(
        queryset=Doador._meta.get_field('congregacao_fk').remote_field.model.objects.all(),
        widget=AutocompleteSelect(
                Doador._meta.get_field('congregacao_fk'),
                admin.site,
                attrs={'data-autocomplete-light-function': 'select2'}
            ),
        required=True,
        label="Congregação",
    )

    class Meta:
        model = Doador
        fields = '__all__'


class DoacaoFormAdmin(forms.ModelForm):    
    valor = forms.CharField(widget=forms.TextInput(attrs={'class': 'vTextField money'}))
    campanha = forms.ModelChoiceField(
        queryset=Campanha.objects.all(),
        widget=AutocompleteSelect(
                Contribuinte._meta.get_field('campanha'),
                admin.site,
                attrs={'data-autocomplete-light-function': 'select2'}
            ),
        required=True,
        label="Campanha",
    )

    doador = forms.ModelChoiceField(
        queryset=Doador.objects.all(),
        widget=AutocompleteSelect(
                Contribuinte._meta.get_field('doador'),
                admin.site,
                attrs={'data-autocomplete-light-function': 'select2'}
            ),
        required=True,
        label="Contribuinte",
    )
    
    
    def clean_valor(self):
        v = self.cleaned_data.get('valor', '')
        # remove 'R$', espaços, separador de milhares, converte vírgula->ponto
        normalized = v.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return Decimal(normalized)

    class Meta:
        model = Doacao        
        fields = ('campanha', 'doador', 'valor', 'data_doacao', 'metodo', 'mes', 'ano', 'recebido_por', 'prestado_contas')
    class Media:
         js = [
            # AutoNumeric CDN (exemplo); pode usar outra versão / Cleave.js
            'https://cdn.jsdelivr.net/npm/autonumeric@4.6.0/dist/autoNumeric.min.js',
            'js/admin-money.js',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # when editing an existing Doacao, populate contribuinte/campanha from the related CampanhaDoador
        if self.instance and getattr(self.instance, 'pk', None):
            camp_doador = getattr(self.instance, 'contribuinte', None)
            if camp_doador:
                self.fields['doador'].initial = camp_doador.doador
                self.fields['campanha'].initial = camp_doador.campanha

        # Set initial values for mes and ano to current month and year
        today = date.today()
        if 'mes' in self.fields:
            self.fields['mes'].initial = today.month
        if 'ano' in self.fields:
            self.fields['ano'].initial = today.year
            
    def save(self, commit=True):
        # Extract the selected contribuinte and campanha and ensure a CampanhaDoador exists
        doador = self.cleaned_data.pop('doador')
        campanha = self.cleaned_data.pop('campanha')

        contribuinte, _ = Contribuinte.objects.get_or_create(
            campanha=campanha, doador=doador
        )

        instance = super().save(commit=False)
        instance.contribuinte = contribuinte
        if commit:
            instance.save()
        return instance