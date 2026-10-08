// Ponto de entrada do dashboard.
// Os módulos são carregados em ordem porque usam funções globais entre si.
const modules = [
  "core.js",
  "data.js",
  "filters.js",
  "cards.js",
  "panels.js",
  "server-panel.js",
  "service-details.js",
  "bootstrap.js",
];

const appScript = document.currentScript;
const modulesPath = new URL("modules/", appScript.src);

for (const moduleName of modules) {
  const script = document.createElement("script");
  script.src = new URL(moduleName, modulesPath);
  script.async = false;
  document.head.appendChild(script);
}
