document.addEventListener('DOMContentLoaded',()=>{const toggle=document.getElementById('menu-toggle'),sidebar=document.getElementById('sidebar');if(toggle)toggle.addEventListener('click',()=>sidebar.classList.toggle('open'));const tooltips=document.querySelectorAll('[data-bs-toggle="tooltip"]');tooltips.forEach(el=>new bootstrap.Tooltip(el));});
async function apiFetch(url, options={}){const response=await fetch(url,options);let body={};try{body=await response.json()}catch(e){}if(!response.ok)throw new Error(body.error||`Request failed (${response.status})`);return body}
function showToast(message){const el=document.createElement('div');el.className='toast show';el.innerHTML=`<div class="toast-body"><i class="bi bi-exclamation-circle me-2"></i>${message}</div>`;document.getElementById('toast-container').appendChild(el);setTimeout(()=>el.remove(),5000)}
function fmtPct(value){return value==null?'Not measured':`${Number(value).toFixed(2)}%`}
function periodText(period){return period?`${period.from} → ${period.to}`:'Not provided'}
function version(versions,key){return versions?.[key]||'Not reported'}
window.DobbyCharts = {
  options() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {grid: {color: '#232d49'}, ticks: {color: '#8e98b5'}},
        y: {grid: {color: '#232d49'}, ticks: {color: '#8e98b5'}}
      },
      plugins: {
        legend: {labels: {color: '#cbd2e8', usePointStyle: true}}
      }
    };
  }
};
