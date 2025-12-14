from django.core.management.base import BaseCommand
from core.models import Doador, Congregacao


class Command(BaseCommand):
    help = 'Atualiza o campo congregacao dos Doadores para usar FK com Congregacao'

    def handle(self, *args, **options):
        doadores = Doador.objects.all()
        count = 0
        for doador in doadores:
            nome_congregacao = getattr(doador, 'congregacao', None)
            if nome_congregacao:
                congregacao_obj, created = Congregacao.objects.get_or_create(nome=nome_congregacao)
                doador.congregacao_fk = congregacao_obj
                doador.save(update_fields=['congregacao_fk'])
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Atualizados {count} doadores com FK de Congregacao.'))