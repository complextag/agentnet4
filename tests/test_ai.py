import importlib, os, sys
from fastapi.testclient import TestClient

def test_ai_routine_and_approval(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH',str(tmp_path/'ai.sqlite3'))
    monkeypatch.setenv('OPENAI_API_KEY','test-key-not-real')
    if 'app' in sys.modules: del sys.modules['app']
    m=importlib.import_module('app')
    client=TestClient(m.app)
    def register(handle):
        r=client.post('/api/register',json={'handle':handle,'display_name':handle,'password':'testpass123'})
        assert r.status_code==201,r.text
        return {'Authorization':'Bearer '+r.json()['token']}
    alice=register('alice'); bob=register('bob')
    r=client.put('/api/ai/settings',headers=bob,json={'enabled':True,'mode':'semi','notes':'Friendly and brief'})
    assert r.status_code==200 and r.json()['enabled']
    monkeypatch.setattr(m,'call_ai',lambda t,recent,settings:('What kind of discussion do you have in mind?',False))
    r=client.post('/api/tasks',headers=alice,json={'recipient':'bob','title':'Hello there','details':'Could we discuss the research?', 'kind':'general'})
    assert r.status_code==201,r.text
    id=r.json()['id']
    thread=client.get(f'/api/tasks/{id}',headers=alice).json()['messages']
    assert len(thread)==2 and thread[-1]['handle']=='bob' and thread[-1]['body'].startswith('[AI agent · semi]')
    monkeypatch.setattr(m,'call_ai',lambda t,recent,settings:('I can approve payment of $500.',False))
    assert client.post(f'/api/tasks/{id}/messages',headers=alice,json={'body':'What is the price?'}).status_code==201
    thread=client.get(f'/api/tasks/{id}',headers=alice).json()['messages']
    assert len(thread)==3
    drafts=client.get('/api/ai/drafts',headers=bob).json()
    assert len(drafts)==1 and drafts[0]['status']=='pending'
    draftid=drafts[0]['id']
    assert client.post(f'/api/ai/drafts/{draftid}/decide',headers=alice,json={'decision':'send'}).status_code==404
    assert client.post(f'/api/ai/drafts/{draftid}/decide',headers=bob,json={'decision':'reject'}).json()['status']=='rejected'
    assert len(client.get(f'/api/tasks/{id}',headers=alice).json()['messages'])==3
    assert client.post(f'/api/ai/drafts/{draftid}/decide',headers=bob,json={'decision':'send'}).status_code==409

def test_ai_disabled_without_key(tmp_path,monkeypatch):
    monkeypatch.setenv('DATABASE_PATH',str(tmp_path/'no_key.sqlite3'))
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    if 'app' in sys.modules: del sys.modules['app']
    m=importlib.import_module('app')
    c=TestClient(m.app)
    r=c.post('/api/register',json={'handle':'nexa','display_name':'Nexa','password':'pass123456'})
    auth={'Authorization':'Bearer '+r.json()['token']}
    assert c.put('/api/ai/settings',headers=auth,json={'enabled':True}).status_code==503
