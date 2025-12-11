from django import forms

from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib import admin
from core.models import CampanhaDoador, Doacao, Doador, Campanha


class DoacaoFormAdmin(forms.ModelForm):
    contribuinte = forms.ModelChoiceField(
        queryset=Doador.objects.all(),
        label="Contribuinte",
        widget=AutocompleteSelect(
            CampanhaDoador._meta.get_field('contribuinte').remote_field,
            admin_site=admin.site
        )
    )

    class Meta:
        model = Doacao
        # include the virtual fields plus the real Doacao fields you want the admin to edit
        fields = ('contribuinte', 'valor', 'metodo', 'data_doacao')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # when editing an existing Doacao, populate contribuinte/campanha from the related CampanhaDoador
        if self.instance and getattr(self.instance, 'pk', None):
            camp_doador = getattr(self.instance, 'doador', None)
            if camp_doador:
                self.fields['contribuinte'].initial = camp_doador.contribuinte
                # self.fields['campanha'].initial = camp_doador.campanha

    def save(self, commit=True):
        # extract virtual fields and create/get the CampanhaDoador
        contribuinte = self.cleaned_data.pop('contribuinte')
        campanha = self.cleaned_data.pop('campanha')

        camp_doador, _ = CampanhaDoador.objects.get_or_create(
            campanha=campanha, contribuinte=contribuinte
        )

        instance = super().save(commit=False)
        instance.doador = camp_doador
        if commit:
            instance.save()
        return instance