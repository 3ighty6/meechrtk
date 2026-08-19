(() => {
  // MeechRTK: no in-page UI. All controls live in the browser extension popup.
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
  window.MeechRTK={optimize};
})();
