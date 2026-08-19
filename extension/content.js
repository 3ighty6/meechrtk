(() => {
  const STOP=/^(the|a|an|and|or|but|if|then|than|this|that|with|from|for|into|your|you|are|was|were|have|has|had|not|can|will|would|should|could|to|of|in|on|is|it|as|be|by|at|we|i|my|me)$/i;
  const words=s=>(s.toLowerCase().match(/[a-z0-9_'-]{3,}/g)||[]).filter(w=>!STOP.test(w));
  const sim=(a,b)=>{const A=new Set(words(a)),B=new Set(words(b));if(!A.size||!B.size)return 0;let n=0;for(const x of A)if(B.has(x))n++;return n/(A.size+B.size-n)};
  function optimize(text,mode='balanced'){
    const lines=text.split(/\r?\n/),out=[],seen=[];let removed=0;
    const threshold=mode==='aggressive'?.82:mode==='conservative'?.96:.90;
    for(const line of lines){const t=line.trim();if(!t){if(out[out.length-1]!=='')out.push('');continue;}
      const important=/\b(error|fatal|failed|failure|exception|traceback|warning|warn|denied|unauthorized|forbidden|not found|cannot|could not|npm ERR|ERR!)\b/i.test(line)||/[A-Z]:\\|\/(?:home|usr|var|etc)\//.test(line);
      if(!important&&seen.some(x=>sim(t,x)>=threshold)){removed++;continue} seen.push(t);out.push(line);
    }
    return {text:out.join('\n').replace(/\n{3,}/g,'\n\n'),removed};
  }
  const isEditable=el=>el&&(el.matches?.('textarea,[contenteditable="true"]')||el.getAttribute?.('role')==='textbox');
  const getText=el=>el.matches?.('textarea')?el.value:el.innerText||el.textContent||'';
  const setText=(el,text)=>{
    if(el.matches?.('textarea')){const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;if(setter)setter.call(el,text);else el.value=text;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));}
    else{el.focus();document.execCommand('selectAll',false);document.execCommand('insertText',false,text);el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:text}));}
  };
  let current=null,bar=null,lastOriginal='';
  function removeBar(){if(bar){bar.remove();bar=null;}current=null;}
  function ensureBar(el){
    if(current===el&&bar)return;
    removeBar();current=el;
    bar=document.createElement('div');bar.dataset.meechrtk='1';
    Object.assign(bar.style,{position:'fixed',zIndex:2147483647,display:'flex',gap:'6px',alignItems:'center',padding:'5px 7px',border:'1px solid rgba(128,128,128,.35)',borderRadius:'10px',background:'rgba(20,20,24,.94)',color:'#fff',font:'12px system-ui',boxShadow:'0 4px 18px rgba(0,0,0,.25)',cursor:'grab',userSelect:'none'});
    const select=document.createElement('select');['conservative','balanced','aggressive'].forEach(x=>{const o=document.createElement('option');o.value=x;o.textContent=x[0].toUpperCase()+x.slice(1);if(x==='balanced')o.selected=true;select.appendChild(o)});Object.assign(select.style,{background:'#222',color:'#fff',border:'0'});
    const optimizeBtn=document.createElement('button');optimizeBtn.textContent='🧙 Optimize';
    const restoreBtn=document.createElement('button');restoreBtn.textContent='↩ Restore';
    const stat=document.createElement('span');stat.textContent='Ready';
    const minBtn=document.createElement('button');minBtn.textContent='—';minBtn.title='Minimize';
    const closeBtn=document.createElement('button');closeBtn.textContent='×';closeBtn.title='Close';
    [optimizeBtn,restoreBtn,minBtn,closeBtn].forEach(b=>Object.assign(b.style,{border:'0',borderRadius:'7px',padding:'5px 8px',cursor:'pointer'}));
    optimizeBtn.onclick=e=>{e.stopPropagation();const original=getText(el);if(!original.trim())return;lastOriginal=original;const r=optimize(original,select.value);setText(el,r.text);const pct=original.length?((1-r.text.length/original.length)*100):0;stat.textContent=`${pct.toFixed(1)}% shorter • ${r.removed} lines`};
    restoreBtn.onclick=e=>{e.stopPropagation();if(lastOriginal){setText(el,lastOriginal);stat.textContent='Restored'}};
    minBtn.onclick=e=>{e.stopPropagation();[select,optimizeBtn,restoreBtn,stat].forEach(x=>x.style.display='none');minBtn.textContent='🧙';minBtn.title='Restore MeechRTK'};
    minBtn.addEventListener('dblclick',e=>{e.stopPropagation();[select,optimizeBtn,restoreBtn,stat].forEach(x=>x.style.display='');minBtn.textContent='—';minBtn.title='Minimize'});
    closeBtn.onclick=e=>{e.stopPropagation();removeBar()};
    bar.append(select,optimizeBtn,restoreBtn,stat,minBtn,closeBtn);document.body.appendChild(bar);
    let dragging=false,dx=0,dy=0;
    bar.addEventListener('pointerdown',e=>{if(e.target.closest('button,select'))return;dragging=true;bar.style.cursor='grabbing';const r=bar.getBoundingClientRect();dx=e.clientX-r.left;dy=e.clientY-r.top;bar.setPointerCapture(e.pointerId)});
    bar.addEventListener('pointermove',e=>{if(!dragging)return;bar.style.left=Math.max(0,e.clientX-dx)+'px';bar.style.top=Math.max(0,e.clientY-dy)+'px';});
    bar.addEventListener('pointerup',()=>{dragging=false;bar.style.cursor='grab'});
    const position=()=>{if(dragging)return;const r=el.getBoundingClientRect();bar.style.left=Math.max(8,r.left)+'px';bar.style.top=Math.max(8,r.top-48)+'px'};position();window.addEventListener('scroll',position,{passive:true});window.addEventListener('resize',position);
  }
  document.addEventListener('focusin',e=>{if(isEditable(e.target))ensureBar(e.target)},true);
  new MutationObserver(()=>{const el=document.activeElement;if(isEditable(el))ensureBar(el)}).observe(document.documentElement,{subtree:true,childList:true});
  window.MeechRTK={optimize};
})();
