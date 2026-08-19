const status=document.getElementById('status'),stats=document.getElementById('stats');
const setStatus=(text,ok=false)=>{status.textContent=text;status.className='stat '+(ok?'ok':'err')};
async function send(type){
  const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
  if(!tab?.id){setStatus('No active tab.');return null;}
  if(!/^https:\/\/(claude\.ai|chatgpt\.com|chat\.openai\.com)\//.test(tab.url||'')){setStatus('Open Claude.ai first, then click the MeechRTK extension icon.');return null;}
  try{return await chrome.tabs.sendMessage(tab.id,{type,mode:document.getElementById('mode').value});}
  catch(e){setStatus('MeechRTK is not connected to this tab. Reload the Claude.ai tab once, then try again.');return null;}
}
document.getElementById('optimize').addEventListener('click',async()=>{
  stats.textContent='';setStatus('Optimizing…',true);const r=await send('MEECHRTK_OPTIMIZE');if(!r)return;
  if(!r.ok){setStatus(r.error);return;}
  const pct=r.originalLength?((1-r.optimizedLength/r.originalLength)*100):0;
  setStatus(r.unchanged?'No redundant content detected.':'Claude message optimized.',true);
  stats.textContent=`${pct.toFixed(1)}% shorter • ${r.originalLength.toLocaleString()} → ${r.optimizedLength.toLocaleString()} characters • ~${r.estimatedOriginalTokens.toLocaleString()} → ~${r.estimatedOptimizedTokens.toLocaleString()} tokens • ${r.removed} lines removed`;
});
document.getElementById('restore').addEventListener('click',async()=>{
  stats.textContent='';setStatus('Restoring…',true);const r=await send('MEECHRTK_RESTORE');if(!r)return;
  if(!r.ok){setStatus(r.error);return;}setStatus('Original Claude message restored.',true);
});
