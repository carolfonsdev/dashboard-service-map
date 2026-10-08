// ── FILTROS ──
function toggleInfra(e){
  e.stopPropagation();
  document.getElementById('infraFilters').classList.toggle('open');
}

document.addEventListener('click',function(e){
  const infra=document.getElementById('infraFilters');
  if(infra && !infra.contains(e.target)) infra.classList.remove('open');
});

function setTech(v,el){
  techFilter=v;
  document.querySelectorAll("[data-tech]").forEach(b=>b.classList.remove("on"));
  el.classList.add("on");
  render();
}

function tecnologiasDoServico(s){
  // Detecta tecnologias por palavras/nomes completos, evitando falsos positivos
  // como "java" dentro de "javascript" ou "go" dentro de outras palavras.
  const texto=[s.type,s.typeKey,s.runtime,s.deps,s.ctx,s.name].join(" ").toLowerCase();
  const tem=(...termos)=>termos.some(t=>new RegExp("(?:^|[^a-z0-9])"+t+"(?:$|[^a-z0-9])","i").test(texto));
  return {
    java: tem("java"),
    node: tem("node","node.js"),
    python: tem("python","python3"),
    react: tem("react","react.js"),
    typescript: tem("typescript","ts","tsx"),
    javascript: tem("javascript","js")
  };
}
function toggleConn(v,el){
  if(connFilters.has(v)){connFilters.delete(v);el.classList.remove("on");}
  else{connFilters.add(v);el.classList.add("on");}render();
}
function matches(s){
  const q=(document.getElementById("search")?.value||"").toLowerCase().trim();
  if(q&&![s.name,s.ctx,s.type,s.deps].join(" ").toLowerCase().includes(q))return false;
  if(techFilter!=="all"&&!tecnologiasDoServico(s)[techFilter])return false;
  for(const c of connFilters)if(!s.conns.includes(c))return false;
  return true;
}

