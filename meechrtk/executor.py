from __future__ import annotations
import json, os, time, urllib.request, urllib.error

class ProviderError(RuntimeError): pass

class Executor:
    def __init__(self):
        self.defaults={
            'claude':('ANTHROPIC_API_KEY','https://api.anthropic.com/v1/messages',os.getenv('MEECHRTK_CLAUDE_MODEL','claude-sonnet-5')),
            'openai':('OPENAI_API_KEY','https://api.openai.com/v1/responses',os.getenv('MEECHRTK_OPENAI_MODEL','gpt-5.6-luna')),
            'xai':('XAI_API_KEY','https://api.x.ai/v1/responses',os.getenv('MEECHRTK_XAI_MODEL','grok-4.6')),
            'google':('GEMINI_API_KEY','https://generativelanguage.googleapis.com/v1beta',os.getenv('MEECHRTK_GOOGLE_MODEL','gemini-2.5-flash')),
            'openrouter':('OPENROUTER_API_KEY','https://openrouter.ai/api/v1/chat/completions',os.getenv('MEECHRTK_OPENROUTER_MODEL','openai/gpt-5.6')),
        }
    def execute(self, provider, prompt, max_output_tokens=2048, reasoning='auto', model=None):
        provider=(provider or 'openrouter').lower(); started=time.time()
        if provider in ('ollama','lmstudio'): result=self._local(provider,prompt,max_output_tokens,model)
        elif provider in self.defaults:
            keyenv,url,default_model=self.defaults[provider];key=os.getenv(keyenv)
            if not key: raise ProviderError(f'{keyenv} is not configured')
            result=self._cloud(provider,key,url,prompt,max_output_tokens,reasoning,model or default_model)
        else: raise ProviderError(f'Unsupported execution provider: {provider}')
        result['latency_ms']=round((time.time()-started)*1000,1);result['provider']=provider;return result
    def _cloud(self,p,key,url,prompt,max_tokens,reasoning,model):
        if p=='claude':
            body={'model':model,'max_tokens':max_tokens,'messages':[{'role':'user','content':prompt}]}
            if reasoning in ('low','medium','high'):body['thinking']={'type':'enabled','budget_tokens':{'low':1024,'medium':4096,'high':8192}[reasoning]}
            headers={'x-api-key':key,'anthropic-version':'2023-06-01'}
        elif p in ('openai','xai'):
            body={'model':model,'input':prompt,'max_output_tokens':max_tokens}
            if reasoning in ('low','medium','high','xhigh','max'):body['reasoning']={'effort':reasoning}
            headers={'Authorization':f'Bearer {key}'}
        elif p=='google':
            url=f"{url}/models/{model}:generateContent?key={key}";body={'contents':[{'role':'user','parts':[{'text':prompt}]}],'generationConfig':{'maxOutputTokens':max_tokens}};headers={}
        else:
            body={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens}
            if reasoning in ('low','medium','high'):body['reasoning_effort']=reasoning
            headers={'Authorization':f'Bearer {key}','X-OpenRouter-Metadata':'enabled'}
        return self._request(url,headers,body,p)
    def _request(self,url,headers,body,p):
        headers={**headers,'Content-Type':'application/json'};req=urllib.request.Request(url,data=json.dumps(body).encode(),headers=headers,method='POST')
        try:
            with urllib.request.urlopen(req,timeout=600) as r:raw=json.loads(r.read());status=r.status
        except urllib.error.HTTPError as e:raise ProviderError(f'{p} HTTP {e.code}: {e.read().decode(errors="replace")[:1000]}')
        except Exception as e:raise ProviderError(f'{p}: {e}')
        return {'text':self._extract(raw,p),'model':raw.get('model'),'usage':self._usage(raw,p),'raw_id':raw.get('id'),'http_status':status}
    def _extract(self,r,p):
        if p=='claude':return ''.join(x.get('text','') for x in r.get('content',[]) if x.get('type')=='text')
        if p in ('openai','xai'):
            if r.get('output_text'):return r['output_text']
            return ''.join(c.get('text','') for x in r.get('output',[]) for c in x.get('content',[]) if c.get('text'))
        if p=='google':return ''.join(part.get('text','') for part in r.get('candidates',[{}])[0].get('content',{}).get('parts',[]))
        if p=='ollama':return r.get('response','')
        return (r.get('choices') or [{}])[0].get('message',{}).get('content','')
    def _usage(self,r,p):
        u=r.get('usage',{}) or {};return {'input_tokens':u.get('input_tokens',u.get('prompt_tokens',u.get('promptTokenCount',0))),'output_tokens':u.get('output_tokens',u.get('completion_tokens',u.get('candidatesTokenCount',0))),'total_tokens':u.get('total_tokens',u.get('totalTokenCount',0))}
    def _local(self,p,prompt,max_tokens,model):
        if p=='ollama':
            url='http://127.0.0.1:11434/api/generate';body={'model':model or os.getenv('MEECHRTK_OLLAMA_MODEL','qwen3:1.7b'),'prompt':prompt,'stream':False,'options':{'num_predict':max_tokens}}
            r=self._request(url,{},body,p);r['model']=body['model'];return r
        url='http://127.0.0.1:1234/v1/chat/completions';body={'model':model or os.getenv('MEECHRTK_LMSTUDIO_MODEL','local-model'),'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens};return self._request(url,{},body,p)
