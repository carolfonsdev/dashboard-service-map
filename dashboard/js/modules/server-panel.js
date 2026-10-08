// ═════ PAINEL SERVIDOR v2 ═════
const esc=t=>String(t).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function watcherOnline(sd){
  if(!sd||sd.watcher!=="online")return false;
  if(!sd.heartbeat)return true;                       // status.json antigo, sem heartbeat
  const idade=Date.now()/1000-sd.heartbeat;
  if(sd.status==="analisando")return idade<600;       // análise longa não é queda
  return idade<Math.max(3*(sd.intervalo||30),30)+10;
}
let osSel=/Win/i.test(navigator.platform)?"win":/Linux/i.test(navigator.platform)?"linux":"mac", actSel="iniciar";
const DEF={mac:["~/Documents/globoads-service-map","~/Repos/back"],linux:["~/globoads-service-map","~/Repos/back"],win:["C:\\Users\\voce\\globoads-service-map","C:\\Repos"]};
function caminhos(){return[document.getElementById("inTools").value.trim()||DEF[osSel][0],document.getElementById("inRepos").value.trim()||DEF[osSel][1]];}
function salvarCaminhos(){try{localStorage.setItem("globoads.caminhos",JSON.stringify([inTools.value,inRepos.value]));}catch{}renderSteps();}
function setOS(os){osSel=os;inTools.placeholder=DEF[os][0];inRepos.placeholder=DEF[os][1];renderSteps();}
function setAct(a){actSel=a;renderSteps();}

function comandos(){
  const [T,R]=caminhos();
  const cd=osSel==="win"?`cd "${T}"`:`cd ${T}`;
  const L=osSel==="mac"?"~/Library/Logs/globoads-service-map":osSel==="linux"?"~/globoads-service-map-logs":"logs";
  const M={
  mac:{
    iniciar:[
      ["Entrar na pasta do Service Map",cd],
      ["Iniciar o Service Map","python3 scripts/instalar_servico.py","O instalador vai pedir a pasta que contém os repositórios. Informe, por exemplo, ~/Documents/Repos. O servidor e o watcher são configurados pelo próprio instalador."]
    ],
    parar:[
      ["Remover o serviço do watcher","python3 scripts/instalar_servico.py --desinstalar","Remove o watcher instalado, mantendo o servidor do dashboard."],
      ["Remover tudo","python3 scripts/instalar_servico.py --desinstalar-tudo","Remove o watcher e o servidor instalados pelo Service Map."]
    ],
    logs:[
      ["Acompanhar os logs",`tail -f ${L}/*.log`],
      ["Só erros",`tail -f ${L}/*-erro.log`],
      ["Verificar se o servidor está no ar","curl localhost:8080/ping"],
      ["Ver status do serviço","python3 scripts/instalar_servico.py --status"]
    ]
  },
  linux:{
    iniciar:[
      ["Entrar na pasta do Service Map",cd],
      ["Iniciar o Service Map",`python3 scripts/instalar_servico.py --rodar --pasta ${R}`,"No Linux o instalador não cria serviço automático. Este comando inicia o servidor e o watcher neste terminal."]
    ],
    parar:[
      ["Parar o Service Map","Ctrl+C","Pare o processo no terminal onde o Service Map está rodando. O último snapshot continua salvo."]
    ],
    logs:[
      ["Verificar se o servidor está no ar","curl http://localhost:8080/ping","Os logs do servidor e do watcher aparecem no mesmo terminal em que o comando --rodar está executando."],
      ["Ver status dos dados","curl http://localhost:8080/status.json","Mostra o total de repositórios, última análise e estado do watcher."]
    ]
  },
  win:{
    iniciar:[
      ["Entrar na pasta do Service Map",cd],
      ["Iniciar o Service Map",`python scripts\instalar_servico.py --rodar --pasta "${R}"`,"No Windows o instalador não cria serviço automático. Este comando inicia o servidor e o watcher neste terminal."]
    ],
    parar:[
      ["Parar o Service Map","Ctrl+C","Pare o processo no PowerShell onde o Service Map está rodando. O último snapshot continua salvo."]
    ],
    logs:[
      ["Verificar se o servidor está no ar","Invoke-RestMethod http://localhost:8080/ping","Os logs do servidor e do watcher aparecem no mesmo PowerShell em que o comando --rodar está executando."],
      ["Ver status dos dados","Invoke-RestMethod http://localhost:8080/status.json","Mostra o total de repositórios, última análise e estado do watcher."]
    ]
  }
  };
  return M[osSel][actSel];
}
function renderSteps(){
  document.querySelectorAll("#osTabs .os-tab").forEach(b=>b.classList.toggle("on",b.dataset.os===osSel));
  document.querySelectorAll("#actTabs .os-tab").forEach(b=>b.classList.toggle("on",b.dataset.act===actSel));
  const num=actSel==="iniciar";
  let out=comandos().map(([lbl,cmd,hint],i)=>`<div class="srv-step"><div class="srv-step-n">${num?i+1:"▪"}</div><div class="srv-step-body">
    <div class="srv-step-label">${esc(lbl)}</div>
    <div class="code-row"><span class="code-txt">${esc(cmd)}</span><button class="copy-btn" title="Copiar" data-cmd="${esc(cmd)}" onclick="cpBtn(this,this.dataset.cmd)"><svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button></div>
    ${hint?`<div class="srv-hint">${esc(hint)}</div>`:""}</div></div>`).join("");
  if(actSel==="logs")out+=`<div class="srv-hint" style="margin-top:12px"><b>OK em 12.3s — 67 repos</b>: análise concluída.<br><b>Mudança detectada</b>: o watcher viu alteração e vai reanalisar.<br><b>Análise falhou</b>: o snapshot anterior foi mantido; a causa está no log de erro.</div>`;
  document.getElementById("srvSteps").innerHTML=out;
}
async function pollPainel(){
  let ping=false,st=null;
  try{ping=(await fetch("/ping?t="+Date.now(),{signal:AbortSignal.timeout(2000)})).ok;}catch{}
  try{const r=await fetch("/status.json?t="+Date.now(),{signal:AbortSignal.timeout(2000)});if(r.ok)st=await r.json();}catch{}
  const wOn=watcherOnline(st), analis=wOn&&st.status==="analisando";
  const row=(cls,nome,sub)=>`<div class="svc-row"><span class="srv-dot ${cls}"></span><div><div class="svc-name">${nome}</div><div class="svc-sub">${sub}</div></div></div>`;
  const semServ=location.protocol==="file:";
  const sub=st?[st.ultima_atualizacao?`última análise ${esc(st.ultima_atualizacao)}`:"",st.total_repos?`${st.total_repos} repos`:"",st.runs?`${st.runs} análise${st.runs>1?"s":""} nesta sessão`:"",st.status==="erro"?"<b>última análise falhou</b> (veja o log de erro)":""].filter(Boolean).join(" · "):"";
  document.getElementById("svcStatus").innerHTML=
    row(ping?"ok":"off","Servidor do dashboard",ping?"respondendo em "+esc(location.host):semServ?"você abriu o HTML direto do disco; inicie o servidor e acesse por localhost":"sem resposta em "+esc(location.host))+
    row(analis?"warn":wOn?"ok":"off","Watcher",analis?"analisando os repositórios…":wOn?(sub||"online"):"parado. O dashboard mostra o último snapshot"+(st&&st.ultima_atualizacao?` (${esc(st.ultima_atualizacao)})`:""));
  document.getElementById("hdrDot").className="srv-dot "+(ping&&wOn?"ok":ping||wOn?"warn":"off");
}
(function initPainel(){
  try{const c=JSON.parse(localStorage.getItem("globoads.caminhos")||"null");if(c){inTools.value=c[0]||"";inRepos.value=c[1]||"";}}catch{}
  setOS(osSel);pollPainel();setInterval(pollPainel,5000);
})();

