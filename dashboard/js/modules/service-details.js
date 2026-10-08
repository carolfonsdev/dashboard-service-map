// ═════ DETALHE DO APP: fatos rápidos, endpoints, quem chama quem, Kafka ═════
const norm=t=>String(t).toLowerCase().replace(/\$\{[^}]*\}/g,"").replace(/[^a-z0-9]/g,"");
function relacoes(s){
  const alvo=n=>{const k=norm(n);return k&&SERVICES.find(o=>o!==s&&(norm(o.name)===k||(k.length>=5&&norm(o.name).includes(k))));};
  const chama=s.calls.map(n=>({n,svc:alvo(n)}));
  const chamadoPor=SERVICES.filter(o=>o!==s&&o.calls.some(n=>{const k=norm(n),me=norm(s.name);return k&&(me===k||(k.length>=5&&me.includes(k)));}));
  return{chama,chamadoPor};
}
function nomeChip(x){return`<button class="rel-chip" onclick="openPanel('${x.replace(/'/g,"\\'")}')">${esc(x)}</button>`;}
function quickFacts(s){
  const obs=[/actuator/i.test(s.deps)&&"Actuator (health)",/springdoc|swagger/i.test(s.deps)&&"Swagger/OpenAPI",/opentelemetry/i.test(s.deps)&&"OpenTelemetry"].filter(Boolean).join(", ");
  const f=[["runtime",s.runtime],["porta",s.port],["observab.",obs],["branch",s.gitBranch],["último commit",s.gitCommit]].filter(x=>x[1]);
  let g=f.map(([k,v])=>`<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");
  return g?`<dl class="facts">${g}</dl>`:"";
}
function depthSections(s){
  let o="";
  const {chama,chamadoPor}=relacoes(s);
  if(chama.length||chamadoPor.length){
    o+=`<div class="psec"><div class="psec-title">relações</div>`;
    if(chama.length)o+=`<div class="rel-lbl">chama (${chama.length})</div><div>${chama.map(c=>c.svc?nomeChip(c.svc.name):`<span class="rel-chip" title="não é um dos repos analisados">${esc(c.n)}</span>`).join("")}</div>`;
    if(chamadoPor.length)o+=`<div class="rel-lbl" style="margin-top:8px">é chamado por (${chamadoPor.length})</div><div>${chamadoPor.map(c=>nomeChip(c.name)).join("")}</div>`;
    o+=`</div>`;
  }
  if(s.epList.length){
    const ep=e=>{const [m,...r]=e.split(" ");return`<div class="ep"><span class="ep-m ep-${esc(m)}">${esc(m)}</span><span>${esc(r.join(" "))}</span></div>`;};
    const top=s.epList.slice(0,8).map(ep).join(""), rest=s.epList.slice(8);
    o+=`<div class="psec"><div class="psec-title">endpoints (${s.epList.length})</div>${top}${rest.length?`<details class="more"><summary>ver mais ${rest.length}</summary>${rest.map(ep).join("")}</details>`:""}</div>`;
  }
  return o;
}
