// ── constantes ──
const CC={Kafka:"b-kafka","Pub/Sub":"b-pubsub",Redis:"b-redis",SQL:"b-sql",MongoDB:"b-mongo",GCS:"b-gcs",Feign:"b-feign",gRPC:"b-grpc"};
const CI={Kafka:"⚡","Pub/Sub":"☁️",Redis:"🔴",SQL:"🗄️",MongoDB:"🍃",GCS:"📁",Feign:"🔗",gRPC:"⚙️"};
const TI={Java:"☕","Node.js":"🌱",Python:"🐍",React:"🦋",TypeScript:"📘",JavaScript:"🌟",Kotlin:"🟣",Go:"🐹",Terraform:"🏗️",Rust:"🦀",Ruby:"💎",PHP:"🐘",".NET":"🔷",Scala:"🔺"};
const TC_L={Java:"#1a6fc4","Node.js":"#15803d",Python:"#b45309",React:"#61dafb",TypeScript:"#3178c6",JavaScript:"#d4a800",Kotlin:"#7f52ff",Go:"#00add8",Terraform:"#7b42bc",Rust:"#b7410e",Ruby:"#cc342d",PHP:"#777bb4",".NET":"#512bd4",Scala:"#dc322f"};
const TC_D={Java:"#60a5fa","Node.js":"#4ade80",Python:"#fbbf24",React:"#61dafb",TypeScript:"#60a5fa",JavaScript:"#facc15",Kotlin:"#a78bfa",Go:"#22d3ee",Terraform:"#a78bfa",Rust:"#fb923c",Ruby:"#f87171",PHP:"#a5b4fc",".NET":"#a78bfa",Scala:"#f87171"};

// ── estado ──
let SERVICES=[], maxLoc=1, techFilter="all", connFilters=new Set(), activeCard=null;
let dropVisible=false, postitVisible=false, srvOpen=false;
let ultimaAtt=null, modoServidor=false;

// ── tema segue o sistema ──
let themeOverride=null;
function isDark(){return themeOverride!==null?themeOverride:window.matchMedia("(prefers-color-scheme:dark)").matches}
function applyTheme(){
  document.documentElement.setAttribute("data-theme",isDark()?"dark":"light");
  document.getElementById("themeIco").innerHTML=isDark()
    ?'<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'
    :'<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>';
}
function toggleTheme(){themeOverride=!isDark();applyTheme();}
window.matchMedia("(prefers-color-scheme:dark)").addEventListener("change",()=>{if(themeOverride===null)applyTheme();});
applyTheme();

// ── ESTADOS DO SISTEMA ──
// online    → watcher ativo, dados atualizados automaticamente
// atualizando → watcher detectou mudança, processando
// offline   → watcher indisponível, exibindo último snapshot
// sem-dados → sem snapshot algum, instalação nova

const ESTADOS = {
  online:       { dot:"ok",       label:"🟢 Watcher online",       sub:"Dados atualizados automaticamente" },
  atualizando:  { dot:"loading",  label:"🟡 Atualizando dados…",   sub:"Aguarde, processando repositórios" },
  offline:      { dot:"offline",  label:"💤 Watcher offline",      sub:"Exibindo último estado conhecido" },
  "sem-dados":  { dot:"sem-dados",label:"⚠️ Nenhum dado disponível",sub:"O watcher ainda não gerou o primeiro snapshot" },
};

function setEstado(estado, subExtra){
  const e=ESTADOS[estado]||ESTADOS["sem-dados"];
  document.getElementById("bannerDot").className="dot "+e.dot;
  document.getElementById("bannerTxt").textContent=e.label;
  document.getElementById("bannerSub").textContent=subExtra||e.sub;
  // CSV só aparece no estado sem-dados
  document.getElementById("dropLink").style.display=estado==="sem-dados"?"inline":"none";
}

