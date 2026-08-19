(() => {
  const STOP=/^(the|a|an|and|or|but|if|then|than|this|that|with|from|for|into|your|you|are|was|were|have|has|had|not|can|will|would|should|could|to|of|in|on|is|it|as|be|by|at|we|i|my|me)$/i;
  const words=s=>(s.toLowerCase().match(/[a-z0-9_'-]{3,}/g)||[]).filter(w=>!STOP.test(w));
  const sim=(a,b)=>{const A=new Set(words(a)),B=new Set(words(b));if(!A.size||!B.size)return 0;let n=0;for(const x of A)if(B.has(x))n++;return n/(A.size+B.size-n)};
  function optimize(text,mode='balanced'){
    const lines=text.split(/\r?\n/),out=[],seen=[];let removed=0;
    const threshold=mode==='aggressive'?.82:mode==='conservative'?.96:.90;
    for(const line of lines){const t=line.trim();if(!t){if(out[out.length-1]!=='')out.push('');continue;}
      const important=/\b(error|fatal|failed|failure|exception|traceback|warning|warn|denied|unauthorized|forbidden|not found|cannot|could not|npm ERR|ERR!)\b/i.test(line)||/[A-Z]:\\|\/(?:home|usr|var|etc)\//.test(line);
      if(!important&&seen.some(x=>sim(t,x)>=threshold)){removed++;continue;} seen.push(t);out.push(line);
    }
    return {text:out.join('\n').replace(/\n{3,}/g,'\n\n'),removed};
  }
  const isEditable=el=>el&&el.nodeType===1&&el.matches?.('textarea,[contenteditable="true"],[role="textbox"]');
  const visible=el=>{if(!isEditable(el))return false;const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';};
  const getText=el=>el.matches('textarea')?el.value:(el.innerText||el.textContent||'');
  function setText(el,text){
    el.focus();
    if(el.matches('textarea')){const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;if(setter)setter.call(el,text);else el.value=text;el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:text}));el.dispatchEvent(new Event('change',{bubbles:true}));return;}
    const sel=getSelection(),range=document.createRange();range.selectNodeContents(el);sel.removeAllRanges();sel.addRange(range);
    let ok=false;try{ok=document.execCommand('insertText',false,text)}catch(_){ok=false}
    if(!ok){range.deleteContents();const node=document.createTextNode(text);range.insertNode(node);range.setStartAfter(node);range.collapse(true);sel.removeAllRanges();sel.addRange(range)}
    el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:text}));
  }
  function findComposer(){
    const active=document.activeElement;if(visible(active))return active;
    const all=[...document.querySelectorAll('textarea,[contenteditable="true"],[role="textbox"]')].filter(visible);
    return all.find(el=>/message|reply|prompt|chat|send/i.test((el.getAttribute('aria-label')||'')+' '+(el.getAttribute('data-placeholder')||'')))||all[all.length-1]||null;
  }
  let lastOriginal='',lastElement=null;
  chrome.runtime.onMessage.addListener((msg,_sender,sendResponse)=>{
    try{
      if(msg?.type==='MEECHRTK_OPTIMIZE'){
        const el=findComposer();if(!el){sendResponse({ok:false,error:'No Claude.ai message box found. Click inside the message box first.'});return true;}
        const original=getText(el);if(!original.trim()){sendResponse({ok:false,error:'The Claude message box is empty.'});return true;}
        const r=optimize(original,msg.mode||'balanced');lastOriginal=original;lastElement=el;setText(el,r.text);
        sendResponse({ok:true,unchanged:r.text===original,originalLength:original.length,optimizedLength:r.text.length,removed:r.removed,estimatedOriginalTokens:Math.ceil(original.length/4),estimatedOptimizedTokens:Math.ceil(r.text.length/4)});return true;
      }
      if(msg?.type==='MEECHRTK_RESTORE'){
        if(!lastOriginal){sendResponse({ok:false,error:'Nothing to restore yet. Optimize a Claude message first.'});return true;}
        const el=visible(lastElement)?lastElement:findComposer();if(!el){sendResponse({ok:false,error:'Claude message box is not available. Click it, then Restore.'});return true;}
        setText(el,lastOriginal);lastOriginal='';lastElement=null;sendResponse({ok:true});return true;
      }
    }catch(e){sendResponse({ok:false,error:`MeechRTK error: ${e.message}`});return true;}
  });
  window.MeechRTK={optimize};
})();
