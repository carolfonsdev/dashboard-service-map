// ── RENDER ──
function render(){
  if(!SERVICES.length)return;
  const f=SERVICES.filter(matches);
  const TC=isDark()?TC_D:TC_L;
  document.getElementById("stats").innerHTML=[
    [f.length,"serviços"],
    [(f.reduce((a,s)=>a+s.loc,0)/1000).toFixed(0)+"k","linhas"],
    [f.reduce((a,s)=>a+s.endpoints,0),"endpoints"],
    [f.reduce((a,s)=>a+s.tests,0).toLocaleString(),"testes"],
  ].map(([n,l])=>`<div class="stat"><span class="stat-n">${n}</span><span class="stat-l">${l}</span></div>`).join("");
  const grid=document.getElementById("grid");
  if(!f.length){grid.innerHTML='<div class="empty">Nenhum resultado 🔍</div>';return;}
  grid.innerHTML=f.map(s=>{
    const vol=Math.round((s.loc/maxLoc)*100);
    const color=TC[s.typeKey]||"#888";
    const badges=s.conns.map(c=>`<span class="badge ${CC[c]||"b-grpc"}">${CI[c]||""} ${c}</span>`).join("");
    return`<div class="card${activeCard===s.name?" active":""}" onclick="openPanel('${s.name.replace(/'/g,"\\'")}')">
      <div class="card-top">
        <div class="card-icon" style="background:${color}15">${TI[s.typeKey]||"⚙️"}</div>
        <div class="card-meta">
          <div class="card-name" title="${s.name}">${s.name}</div>
          <div class="card-type">${s.type} · ${s.disk}</div>
        </div>
      </div>
      ${badges?`<div class="card-badges">${badges}</div>`:""}
      <div class="card-nums">
        <div class="num"><b>${s.loc.toLocaleString()}</b> loc</div>
        <div class="num"><b>${s.endpoints}</b> endpoints</div>
        <div class="num"><b>${s.tests}</b> testes</div>
      </div>
      <div class="vol-bar"><div class="vol-fill" style="width:${vol}%"></div></div>
    </div>`;
  }).join("");
}

