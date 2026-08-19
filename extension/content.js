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
  const isEditable=el=>el&&(el.matches?.('textarea,[contenteditable="true"]')||el.getAttribute?.('role')==='textbox');
  const getText=el=>el?.matches?.('textarea')?el.value:(el?.innerText||el?.textContent||'');
  const setText=(el,text)=>{
    if(el.matches?.('textarea')){const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;if(setter)setter.call(el,text);else el.value=text;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));}
    else{el.focus();document.execCommand('selectAll',false);document.execCommand('insertText',false,text);el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:text}));}
  };
  function findComposer(){
    const active=document.activeElement;if(isEditable(active))return active;
    const candidates=[...document.querySelectorAll('textarea,[contenteditable="true"],[role="textbox"]')].filter(isEditable);
    return candidates.find(el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0})||null;
  }
  chrome.runtime.onMessage.addListener((msg,_sender,sendResponse)=>{
    if(msg?.type==='MEECHRTK_OPTIMIZE'){
      const el=findComposer();if(!el){sendResponse({ok:false,error:'No Claude.ai message box found. Click the message box first, then open MeechRTK.'});return true;}
      const original=getText(el);if(!original.trim()){sendResponse({ok:false,error:'The Claude message box is empty.'});return true;}
      const r=optimize(original,msg.mode||'balanced');setText(el,r.text);
      sendResponse({ok:true,originalLength:original.length,optimizedLength:r.text.length,removed:r.removed});return true;
    }
    if(msg?.type==='MEECHRTK_READ'){
      const el=findComposer();sendResponse({ok:!!el,text:el?getText(el):''});return true;
    }
  });
  window.MeechRTK={optimize};
})();
