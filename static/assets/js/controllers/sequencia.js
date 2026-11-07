angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var COR_ACORDE = '#2E1C74';
  var vm = this;
  vm.sequenciasFamosas = [];
  vm.minhaSequencia = { acordes: [] };
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.esfigeSpeech = "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.progressbar = ngProgressFactory.createInstance();

  vm.carregandoSequencias = false;
  vm.erroSequencias = "";
  vm.novaSequencia = "";
  vm.isCadastrando = false;
  vm.mensagemCadastro = "";
  vm.erroCadastro = "";

  var paraSequencia = function(item) {
    return {
      id: item.id,
      acordes: item.acordes.map(function(acorde) {
        return { acorde: acorde, cor: COR_ACORDE };
      })
    };
  };

  var selecionarSequencia = function(id) {
    for (var i = 0; i < vm.sequenciasFamosas.length; i++) {
      if (vm.sequenciasFamosas[i].id === id) {
        vm.pesquisarPorSequencia(vm.sequenciasFamosas[i]);
        return;
      }
    }
  };

  var carregarSequencias = function(idParaSelecionar) {
    vm.carregandoSequencias = true;
    vm.erroSequencias = "";
    $http.get('sequencias')
      .success(function(data) {
        vm.carregandoSequencias = false;
        vm.sequenciasFamosas = data.map(paraSequencia);
        if (idParaSelecionar) {
          selecionarSequencia(idParaSelecionar);
        }
      })
      .error(function() {
        vm.carregandoSequencias = false;
        vm.erroSequencias = "Não foi possível carregar as sequências.";
      });
  };

  vm.temAcorde = function(acorde) {
    var nome = acorde && acorde.acorde ? acorde.acorde : acorde;
    if (!vm.minhaSequencia.acordes) {
      return false;
    }
    return vm.minhaSequencia.acordes.some(function(item) {
      return item.acorde === nome;
    });
  };

  vm.cadastrarSequencia = function() {
    if (!vm.novaSequencia || !vm.novaSequencia.trim()) {
      vm.erroCadastro = "Informe os acordes da sequência.";
      vm.mensagemCadastro = "";
      return;
    }

    vm.isCadastrando = true;
    vm.erroCadastro = "";
    vm.mensagemCadastro = "";
    $http.post('sequencias', { acordes: vm.novaSequencia })
      .success(function(data, status) {
        vm.isCadastrando = false;
        vm.mensagemCadastro = status === 201 ?
          "Sequência cadastrada." :
          "Essa sequência já estava cadastrada.";
        vm.novaSequencia = "";
        carregarSequencias(data.id);
      })
      .error(function(data) {
        vm.isCadastrando = false;
        vm.erroCadastro = (data && data.erro) ?
          data.erro :
          "Não foi possível cadastrar a sequência.";
      });
  };

  vm.pesquisarPorSequencia = function(sequencia) {
    if (sequencia) {
      vm.minhaSequencia = sequencia;
    }
    if (!vm.minhaSequencia.id) {
      return;
    }

    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.musics = [];
    vm.showSearchResultsCount = false;

    var apiUrl = "";
    var searchString = "similares?sequencia_id=".concat(vm.minhaSequencia.id);
    if (vm.meuGenero !== "" && vm.meuGenero !== null) {
      searchString += "&generos=" + encodeURIComponent(vm.meuGenero);
    }
    $http.get(apiUrl.concat(searchString))
      .success(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = "Encontrei essas músicas";
        vm.isSearching = false;
        vm.showSearchResultsCount = true;
        vm.musics = data;
      })
      .error(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = (data && data.erro) ?
          data.erro :
          "Ops! Algo errado.";
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
      });
  };

  vm.limparPesquisa = function() {
    vm.minhaSequencia = { acordes: [] };
    vm.musics = [];
    vm.showSearchResultsCount = false;
    vm.esfigeSpeech = "";
  };

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };

  carregarSequencias();
});
