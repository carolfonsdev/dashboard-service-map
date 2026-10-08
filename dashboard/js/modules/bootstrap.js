// Inicialização offline-first do dashboard. Deve ser carregada por último.
let ultimoTimestamp=null;
let tentativasOffline=0;
const MAX_TENTATIVAS_ANTES_OFFLINE=2;

setEstado("sem-dados","Carregando…");
const temDadosJS=tentarDadosJS();
if(!temDadosJS){
  setEstado("sem-dados","O watcher ainda não gerou o primeiro snapshot");
  document.getElementById("dropLink").style.display="inline";
}
pollServidor();
setInterval(pollServidor,5000);
