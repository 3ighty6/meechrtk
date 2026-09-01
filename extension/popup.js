const status=document.getElementById('status'),stats=document.getElementById('stats');
const setStatus=(text,ok=false)=>{status.textContent=text;status.className='stat '+(ok?'ok':'err')};
const sites=/^https:\/\/(claude\.ai|chatgpt\.com|chat\.openai\.com|grok\.com|x\.com|gemini\.google\.com)\//i;
async function send(type){
  const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
  if(!tab?.id){setStatus('No active tab.');return null;}
  if(!sites.test(tab.url||'')){setStatus('Open Claude, ChatGPT, Grok, or Gemini first.');return null;}
  try{return await chrome.tabs.sendMessage(tab.id,{type,budget:document.getElementById('mode').value});}
  catch(e){setStatus('MeechRTK is not connected. Reload the AI tab once, then try again.');return null;}
}
(async()=>{const r=await send('MEECHRTK_STATUS');if(r?.ok)setStatus(`Connected • ${r.provider.toUpperCase()}`,true);})();
document.getElementById('optimize').addEventListener('click',async()=>{stats.textContent='';setStatus('Governing context…',true);const r=await send('MEECHRTK_OPTIMIZE');if(!r)return;if(!r.ok){setStatus(r.error);return;}setStatus(`Optimized • ${r.provider.toUpperCase()}`,true);stats.textContent=`${r.reduction.toFixed(1)}% context reduction • ~${r.originalTokens.toLocaleString()} → ~${r.optimizedTokens.toLocaleString()} tokens • ${r.coverage.toFixed(1)}% information coverage`;});
document.getElementById('restore').addEventListener('click',async()=>{stats.textContent='';setStatus('Restoring…',true);const r=await send('MEECHRTK_RESTORE');if(!r)return;if(!r.ok){setStatus(r.error);return;}setStatus('Original request restored.',true);});
