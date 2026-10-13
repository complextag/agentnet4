import importlib,sys
from fastapi.testclient import TestClient

def test_per_account_modes_and_approval(tmp_path,monkeypatch):
    monkeypatch.setenv('DATABASE_PATH',str(tmp_path/'modes.sqlite3'))
    monkeypatch.setenv('OPENAI_API_KEY','fake-test-key')
    sys.modules.pop('app',None)
    m=importlib.import_module('app'); c=TestClient(m.app)
    def reg(handle):
        r=c.post('/api/register',json={'handle':handle,'display_name':handle,'password':'testpass123'})
        assert r.status_code==201,r.text
        return {'Authorization':'Bearer '+r.json()['token']}
    a=reg('alice');b=reg('bob');z=reg('zoe')
    assert c.get('/api/ai/settings',headers=a).json()['enabled']
    assert c.get('/api/ai/settings',headers=b).json()['mode']=='semi'
    assert c.put('/api/ai/settings',headers=b,json={'enabled':True,'mode':'manual'}).status_code==200
    assert c.put('/api/ai/settings',headers=z,json={'enabled':True,'mode':'autonomous'}).status_code==200
    monkeypatch.setattr(m,'call_ai',lambda t,recent,settings:('Here are some ideas: cycling or a museum.',False))
    x=c.post('/api/tasks',headers=a,json={'recipient':'bob','title':'Suggestions','details':'Suggest fun activities','kind':'general'})
    assert x.status_code==201,x.text
    tid=x.json()['id']
    assert len(c.get('/api/tasks/'+str(tid),headers=b).json()['messages'])==1
    drafts=c.get('/api/ai/drafts',headers=b).json()
    assert len(drafts)==1 and drafts[0]['reason'].startswith('Manual')
    assert c.post('/api/ai/drafts/'+str(drafts[0]['id'])+'/decide',headers=b,json={'decision':'send'}).status_code==200
    assert len(c.get('/api/tasks/'+str(tid),headers=b).json()['messages'])==2
    y=c.post('/api/tasks',headers=a,json={'recipient':'zoe','title':'Suggestions','details':'Suggest fun activities','kind':'general'})
    assert y.status_code==201
    thread=c.get('/api/tasks/'+str(y.json()['id']),headers=a).json()['messages']
    assert len(thread)==2 and '[AI agent · autonomous]' in thread[-1]['body']
    monkeypatch.setattr(m,'call_ai',lambda t,recent,settings:('I will pay $400 now.',False))
    c.post('/api/tasks/'+str(y.json()['id'])+'/messages',headers=a,json={'body':'Could you recommend something else?'})
    assert len(c.get('/api/ai/drafts',headers=z).json())==1
    assert c.put('/api/ai/settings',headers=a,json={'mode':'wrong','enabled':True}).status_code==400
