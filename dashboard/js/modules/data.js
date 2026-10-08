// ── CONVERTER dados do script → formato interno ──
function csvRowToSvc(r){
  const conns=(r.Conexoes_detectadas||"").split(",").map(c=>c.trim()).filter(Boolean).map(c=>{
    if(/kafka/i.test(c))return"Kafka";if(/pub.?sub/i.test(c))return"Pub/Sub";
    if(/redis/i.test(c))return"Redis";if(/jdbc|jpa|relacional/i.test(c))return"SQL";
    if(/mongo/i.test(c))return"MongoDB";if(/cloud.storage|gcs/i.test(c))return"GCS";
    if(/feign/i.test(c))return"Feign";if(/grpc/i.test(c))return"gRPC";return null;
  }).filter(Boolean);
  const tk=(r.Tipo||"").replace("/Maven","").replace("/Gradle","");
  return{name:r.Nome||"?",type:r.Tipo||"?",typeKey:tk,
    files:parseInt(r.Num_arquivos_producao)||0,loc:parseInt(r.Num_linhas_codigo)||0,
    endpoints:(r.Endpoints_lista?r.Endpoints_lista.split(" | ").filter(Boolean).length:parseInt(r.Num_endpoints))||0,tests:parseInt(r.Num_testes)||0,
    disk:r.Tamanho_disco||"—",conns:[...new Set(conns)],
    flow:r.Fluxo_simples||"",ctx:r.Descricao_simples||r.README_resumo||"",
    analogy:r.Analogia||"",deps:r.Principais_dependencias||"",docker:r.Dockerfile_base||"",
    epList:(r.Endpoints_lista||"").split(" | ").filter(Boolean),runtime:r.Runtime||"",port:r.Porta||"",
    calls:(r.Chama_apps||"").split(",").map(x=>x.trim()).filter(Boolean),kafka:r.Topicos_kafka||"",
    gitBranch:r.Git_branch||"",gitCommit:r.Git_ultimo_commit||"",gitUrl:r.Git_url||""};
}

function carregarServicos(lista, geradoEm, fonte){
  SERVICES=lista.map(csvRowToSvc);
  maxLoc=Math.max(...SERVICES.map(s=>s.loc),1);
  document.getElementById("stats").style.display="grid";
  document.getElementById("toolbar").style.display="flex";
  document.getElementById("dropZone").classList.remove("show");
  dropVisible=false;

  ultimoTimestamp=geradoEm;

  // estado visual por fonte
  if(fonte==="servidor"){
    setEstado("online", `Última atualização: ${geradoEm}`);
    showToast("✅ Dados atualizados automaticamente");
  } else if(fonte==="dados.js"){
    // dados.js carregado offline — tenta servidor em paralelo
    setEstado("offline", `Último snapshot: ${geradoEm}`);
  } else if(fonte==="manual"){
    setEstado("offline", `CSV importado em ${geradoEm}`);
    showToast("📂 CSV carregado com sucesso!");
  }
  render();
}

// atualiza estado visual sem limpar dados
function setEstadoConexao(statusWatcher){
  if(!SERVICES.length) return; // sem dados — mantém sem-dados
  if(statusWatcher==="online"){
    setEstado("online", `Última atualização: ${ultimoTimestamp||"agora"}`);
  } else if(statusWatcher==="atualizando"){
    setEstado("atualizando");
  } else {
    // offline — mantém dados, apenas muda banner
    setEstado("offline", `Último snapshot: ${ultimoTimestamp||"desconhecido"}`);
  }
}

// ── 1. TENTA dados.js (offline, gerado pelo script) ──
function tentarDadosJS(){
  if(window.GLOBOADS_SERVICE_MAP_DADOS && Array.isArray(window.GLOBOADS_SERVICE_MAP_DADOS.servicos) && window.GLOBOADS_SERVICE_MAP_DADOS.servicos.length){
    const d=window.GLOBOADS_SERVICE_MAP_DADOS;
    carregarServicos(d.servicos, d.gerado_em, "dados.js");
    return true;
  }
  return false;
}

// ── 2. POLLING do servidor ──
async function pollServidor(){
  try{
    // lê status.json — arquivo escrito pelo watcher (não depende de endpoint HTTP do watcher)
    let statusWatcher="desconhecido";
    try{
      const sr=await fetch("/status.json?t="+Date.now(),{cache:"no-store",signal:AbortSignal.timeout(3000)});
      if(sr.ok){
        const sd=await sr.json();
        // status.json existe e watcher escreveu nele → watcher está online
        statusWatcher=watcherOnline(sd)?"online":"desconhecido";
        if(sd.status==="analisando"&&watcherOnline(sd)){
          setEstadoConexao("atualizando");
          return;
        }
      }
    }catch{/* status.json indisponível — watcher offline ou primeira instalação */}

    // /ping checa se o servidor HTTP do Service Map está rodando
    const pingRes=await fetch("/ping?t="+Date.now(),{cache:"no-store",signal:AbortSignal.timeout(2000)}).catch(()=>null);
    if(!pingRes||!pingRes.ok){throw new Error("servidor offline");}
    const res=await fetch("/dashboard/js/repos_analise.csv?t="+Date.now(),{cache:"no-store",signal:AbortSignal.timeout(4000)});
    if(!res.ok)throw new Error();
    const txt=await res.text();
    const sig=txt;

    tentativasOffline=0; // servidor respondeu — reseta contador

    if(sig===ultimaAtt){
      // sem novidade no CSV, mas servidor está online
      if(SERVICES.length) setEstadoConexao(statusWatcher);
      return;
    }
    ultimaAtt=sig;
    modoServidor=true;
    const rows=parseCSV(txt);
    const agora=new Date().toLocaleString("pt-BR",{day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit"}).replace(",","");
    carregarServicos(rows, agora, "servidor");

  }catch{
    tentativasOffline++;
    if(tentativasOffline>=MAX_TENTATIVAS_ANTES_OFFLINE){
      // servidor indisponível — vai para offline sem limpar dados
      if(SERVICES.length){
        setEstadoConexao("offline");
      }
      // se sem dados e sem snapshot: estado sem-dados já definido na init
    }
  }
}

// ── CSV PARSER ──
function parseCSV(t){
  const ls=t.trim().split(/\r?\n/);if(ls.length<2)return[];
  const hs=ls[0].split(",").map(h=>h.trim().replace(/^"|"$/g,""));
  return ls.slice(1).map(l=>{
    const cs=[];let d=false,c="";
    for(let i=0;i<l.length;i++){
      if(l[i]==='"'){d=!d;continue;}
      if(l[i]===','&&!d){cs.push(c);c="";continue;}
      c+=l[i];
    }
    cs.push(c);
    const o={};hs.forEach((h,i)=>o[h]=(cs[i]||"").trim());return o;
  }).filter(r=>r.Nome);
}

// ── DRAG & DROP ──
function toggleDrop(){
  dropVisible=!dropVisible;
  document.getElementById("dropZone").classList.toggle("show",dropVisible);
}
function dzOver(e){e.preventDefault();document.getElementById("dropZone").classList.add("over");}
function dzLeave(e){document.getElementById("dropZone").classList.remove("over");}
function dzDrop(e){
  e.preventDefault();
  document.getElementById("dropZone").classList.remove("over");
  const f=e.dataTransfer.files[0];
  if(f)lerArquivo(f);
}
function onFile(e){const f=e.target.files[0];if(f)lerArquivo(f);}
function lerArquivo(f){
  const r=new FileReader();
  r.onload=ev=>{
    const rows=parseCSV(ev.target.result);
    const agora=new Date().toLocaleString("pt-BR",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"});
    carregarServicos(rows, agora, "manual");
  };
  r.readAsText(f,"utf-8");
}
// drop na página inteira
document.addEventListener("dragover",e=>e.preventDefault());
document.addEventListener("drop",e=>{
  e.preventDefault();
  const f=e.dataTransfer.files[0];
  if(f&&f.name.endsWith(".csv"))lerArquivo(f);
});

