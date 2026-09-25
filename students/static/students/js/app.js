document.addEventListener('DOMContentLoaded',()=>{
  if(window.lucide) lucide.createIcons();
  const sidebar=document.getElementById('sidebar'), menu=document.getElementById('menuButton'), close=document.getElementById('sidebarClose'), overlay=document.getElementById('sidebarBackdrop');
  const hide=()=>{sidebar?.classList.remove('open');overlay?.classList.remove('show')};
  menu?.addEventListener('click',()=>{sidebar?.classList.add('open');overlay?.classList.add('show')});
  close?.addEventListener('click',hide); overlay?.addEventListener('click',hide);
  window.addEventListener('resize',()=>{if(innerWidth>800)hide()});
  document.querySelectorAll('[data-confirm]').forEach(el=>el.addEventListener('click',e=>{if(!confirm(el.dataset.confirm))e.preventDefault()}));

  // Keyboard-friendly global navigation: Ctrl/Cmd + K focuses the search field.
  const globalSearch=document.querySelector('.top-search input');
  document.addEventListener('keydown',e=>{
    if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==='k'){
      e.preventDefault();
      globalSearch?.focus();
      globalSearch?.select();
    }
    if(e.key==='Escape' && document.activeElement===globalSearch) globalSearch.blur();
  });
});
