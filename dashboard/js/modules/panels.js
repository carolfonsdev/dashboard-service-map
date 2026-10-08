// ── SIDE PANEL ──
function buildFlow(f){
  if(!f)return'<span class="flow-chip">—</span>';
  return f.split(/→|->/).map((s,i,a)=>`<span class="flow-chip">${s.trim()}</span>${i<a.length-1?'<span class="flow-arr">→</span>':""}`).join(" ");
}
function openPanel(name){
  const s=SERVICES.find(x=>x.name===name);if(!s)return;
  activeCard=name;render();
  const TC=isDark()?TC_D:TC_L;
  const color=TC[s.typeKey]||"#888";
  const vol=Math.round((s.loc/maxLoc)*100);
  const badges=s.conns.map(c=>`<span class="badge ${CC[c]||"b-grpc"}">${CI[c]||""} ${c}</span>`).join("");
  document.getElementById("pIcon").style.background=color+"18";
  document.getElementById("pIcon").textContent=TI[s.typeKey]||"⚙️";
  document.getElementById("pTitle").textContent=s.name;
  document.getElementById("pSub").textContent=`${s.type} · ${s.disk}`;
  document.getElementById("panelBody").innerHTML=`
    <div class="metrics">
      <div class="metric"><div class="metric-n">${s.loc.toLocaleString()}</div><div class="metric-l">linhas de código</div></div>
      <div class="metric"><div class="metric-n">${s.endpoints}</div><div class="metric-l">endpoints REST</div></div>
      <div class="metric"><div class="metric-n">${s.files}</div><div class="metric-l">arquivos produção</div></div>
      <div class="metric"><div class="metric-n">${s.tests}</div><div class="metric-l">testes</div></div>
    </div>
    <div class="vol-panel">
      <div class="vol-panel-track"><div class="vol-panel-fill" style="width:${vol}%"></div></div>
      <div class="vol-lbl"><span>volume relativo</span><span>${vol}% do maior serviço</span></div>
    </div>
    ${quickFacts(s)}
    ${s.conns.length?`<div class="psec"><div class="psec-title">integrações</div><div class="badge-list">${badges}</div></div>`:""}
    ${s.flow?`<div class="psec"><div class="psec-title">fluxo de dados</div><div class="flow-wrap">${buildFlow(s.flow)}</div></div>`:""}
    ${depthSections(s)}
    ${s.ctx?`<div class="psec"><div class="psec-title">o que ela faz</div><div class="ctx-text">${s.ctx}</div></div>`:""}
    ${s.analogy?`<div class="psec"><div class="psec-title">analogia</div><div class="analogy-box"><strong>💡 Como lembrar</strong>${s.analogy}</div></div>`:""}
  `;
  document.getElementById("overlay").classList.add("show");
  document.getElementById("panel").classList.add("show");
}
function closePanel(){
  activeCard=null;
  document.getElementById("overlay").classList.remove("show");
  document.getElementById("panel").classList.remove("show");
  render();
}

// ── SIDEBAR SERVIDOR ──
function openSrv(){srvOpen=true;document.getElementById("srvOverlay").classList.add("show");document.getElementById("srvPanel").classList.add("show");}
function closeSrv(){srvOpen=false;document.getElementById("srvOverlay").classList.remove("show");document.getElementById("srvPanel").classList.remove("show");}

// ── POSTIT ──
function togglePostit(){
  postitVisible=!postitVisible;
  document.getElementById("postit").classList.toggle("show",postitVisible);
}
document.addEventListener("click",e=>{
  if(!e.target.closest(".postit")&&!e.target.closest(".postit-btn"))
    {postitVisible=false;document.getElementById("postit").classList.remove("show");}
});

// ── COPY BTN ──
function cpBtn(btn,txt){
  navigator.clipboard.writeText(txt).then(()=>{
    const svg=btn.innerHTML;
    btn.classList.add("ok");
    btn.innerHTML='<svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>';
    setTimeout(()=>{btn.classList.remove("ok");btn.innerHTML=svg;},2000);
  });
}

// ── TOAST ──
function showToast(msg){
  const t=document.getElementById("toast");
  t.textContent=msg;t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"),3000);
}

// ── ESC ──
document.addEventListener("keydown",e=>{if(e.key==="Escape"){closePanel();closeSrv();}});

