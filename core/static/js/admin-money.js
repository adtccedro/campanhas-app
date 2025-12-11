document.addEventListener('DOMContentLoaded', function() {
  // Inicializa AutoNumeric em inputs com classe .money
  document.querySelectorAll('input.money').forEach(function(el) {
    // Configuração para Real (R$), separador de milhar = '.', decimal = ','
    new AutoNumeric(el, {
      currencySymbol: 'R$ ',
      decimalCharacter: ',',
      digitGroupSeparator: '.',
      currencySymbolPlacement: 'p',
      decimalPlaces: 2,
      unformatOnSubmit: true  // autoNumeric converte para número limpo ao submeter
    });
  });
});