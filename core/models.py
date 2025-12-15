from django.db import models


class ModelAbstract(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de criação")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última atualização")

    class Meta:
        abstract = True
        
        
class Campanha(ModelAbstract):
    nome = models.CharField(max_length=255, verbose_name="Nome da Campanha")
    descricao = models.TextField(verbose_name="Descrição da Campanha")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Término")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    def __str__(self):
        return self.nome


class Congregacao(ModelAbstract):
    nome = models.CharField(max_length=255, verbose_name="Nome da Congregação")
    endereco = models.CharField(max_length=255, verbose_name="Endereço", null=True, blank=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Congregação'
        verbose_name_plural = 'Congregações'
    

class Doador(ModelAbstract):
    nome = models.CharField(max_length=255, verbose_name="Nome do Doador")
    email = models.EmailField(verbose_name="Email do Doador", null=True, blank=True)
    telefone = models.CharField(max_length=20, verbose_name="Telefone do Doador", null=True, blank=True)
    congregacao = models.CharField(max_length=255, verbose_name="Congregação", null=True, blank=True)
    congregacao_fk = models.ForeignKey(
        Congregacao, on_delete=models.SET_NULL, related_name="doadores", 
        verbose_name="Congregação", null=True, blank=True)
    
    def __str__(self):
        return f"{self.nome} - {self.congregacao_fk}"
    
    class Meta:
        verbose_name = "Doador"
        verbose_name_plural = "Doadores"


class Contribuinte(ModelAbstract):
    campanha = models.ForeignKey(
        Campanha, on_delete=models.CASCADE, related_name="campanha_doador", verbose_name="Campanha")
    doador = models.ForeignKey(
        Doador, on_delete=models.CASCADE, related_name="doadores", verbose_name="Contribuinte")
    
    class Meta:
        unique_together = ('campanha', 'doador')
    
    def __str__(self):
        return f"{self.doador} - {self.campanha}"
    
    
class Doacao(ModelAbstract):        
    class MeioPagamento(models.TextChoices):
        DINHEIRO = 'DINHEIRO', 'Dinheiro'
        PIX = 'PIX', 'PIX'
    
    contribuinte = models.ForeignKey(
        Contribuinte, on_delete=models.CASCADE, related_name="doacoes", verbose_name="Contribuinte")
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor da Doação")
    data_doacao = models.DateField(verbose_name="Data da Doação")
    metodo = models.CharField(
        max_length=100, verbose_name="Método de Pagamento", choices=MeioPagamento.choices, 
        default=MeioPagamento.DINHEIRO)
    mes = models.IntegerField(verbose_name="Mês da Doação", null=True, blank=True)
    ano = models.IntegerField(verbose_name="Ano da Doação", null=True, blank=True)
    prestado_contas = models.BooleanField(
        default=False, verbose_name="Prestado Contas")
    
    def __str__(self):
        return f"{self.contribuinte.doador.nome} - {self.valor}"
    
    class Meta:
        ordering = ['-ano', 'mes']
        verbose_name = "Doação"
        verbose_name_plural = "Doações"