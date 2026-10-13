import importlib, os, sys
from fastapi.testclient import TestClient

def test_full_flow(tmp_path):
    os.environ['DATABASE_PATH']=str(tmp_path/'test.sqlite3')
    if 'app' in sys.modules: del sys.modules['app']
    m=importlib.import_module('app')
    client=TestClient(m.app)
    def user(handle):
        r=client.post('/api/register',json={'handle':handle,'display_name':handle.title(),'password':'safe-pass-123'})
        assert r.status_code==201,r.text
        return {'Authorization':'Bearer '+r.json()['token']}
    a=user('alice');b=user('bob')
    assert len(client.get('/api/agents',headers=a).json())==1
    r=client.post('/api/tasks',headers=a,json={'recipient':'bob','title':'Research meeting','details':'Thursday at 2 PM','kind':'meeting'})
    assert r.status_code==201,r.text
    task=r.json();tid=task['id']
    assert client.get(f'/api/tasks/{tid}',headers=b).status_code==200
    assert client.post(f'/api/tasks/{tid}/decide',headers=a,json={'decision':'approve'}).status_code==403
    assert client.post(f'/api/tasks/{tid}/decide',headers=b,json={'decision':'approve'}).json()['status']=='approved'
    assert client.post(f'/api/tasks/{tid}/messages',headers=a,json={'body':'Confirmed'}).status_code==201
    assert client.post(f'/api/tasks/{tid}/decide',headers=a,json={'decision':'complete'}).json()['status']=='completed'
    assert len(client.get(f'/api/tasks/{tid}',headers=b).json()['messages'])==4
    assert client.get('/api/tasks').status_code==401
    assert client.get('/manifest.webmanifest').status_code==200
