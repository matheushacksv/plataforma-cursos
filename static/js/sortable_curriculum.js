// static/js/sortable_curriculum.js

function initSortableCurriculum(updateUrl, csrfToken) {
    var modulesList = document.getElementById('modules-list');
    
    // Trava de segurança: se a div não existir, não faz nada
    if (!modulesList) return; 

    // 1. Permite arrastar os Módulos
    new Sortable(modulesList, {
        animation: 150,
        handle: '.card-header', 
        onEnd: salvarNovaOrdem 
    });

    // 2. Permite arrastar as Aulas
    var lessonsLists = document.querySelectorAll('.lessons-list');
    lessonsLists.forEach(function(list) {
        new Sortable(list, {
            group: 'aulas', 
            animation: 150,
            onEnd: salvarNovaOrdem 
        });
    });

    // 3. Função que lê a tela e manda pro Django via HTMX
    function salvarNovaOrdem() {
        let estrutura = [];
        
        document.querySelectorAll('.module-item').forEach((modEl, modIndex) => {
            let modId = modEl.dataset.id;
            let aulas = [];
            
            modEl.querySelectorAll('.lesson-item').forEach((aulaEl, aulaIndex) => {
                aulas.push({
                    id: aulaEl.dataset.id,
                    order: aulaIndex
                });
            });

            estrutura.push({
                id: modId,
                order: modIndex,
                aulas: aulas
            });
        });

        let statusEl = document.getElementById('save-status');
        if (statusEl) {
            statusEl.innerText = "⏳ Salvando...";
            statusEl.classList.remove('opacity-0');
        }

        // Usa os parâmetros passados para a função em vez das tags do Django!
        htmx.ajax('POST', updateUrl, {
            values: { 'nova_estrutura': JSON.stringify(estrutura) },
            headers: { 'X-CSRFToken': csrfToken },
            swap: 'none' 
        }).then(() => {
            if (statusEl) {
                statusEl.innerText = "✅ Salvo!";
                setTimeout(() => statusEl.classList.add('opacity-0'), 2000);
            }
        });
    }
}