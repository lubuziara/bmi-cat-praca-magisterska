import copy
import pytest
from sqlalchemy import select
from app.database.models.owner_profile import OwnerProfile
from test_registration import ACCOUNT


def verified(client, email='diary@example.com'):
    payload=copy.deepcopy(ACCOUNT);payload['email']=email
    response=client.post('/api/auth/register',json=payload)
    assert response.status_code==201
    with client.app.state.database.sessions() as db:
        profile=db.get(OwnerProfile,response.json()['user']['id'])
        profile.email_verified=True;profile.phone_verified=True;db.commit()
    return {'Authorization':'Bearer '+response.json()['access_token']}


def test_diary_persists_scales_and_isolates_dates_and_owners(client):
    headers=verified(client)
    path='/api/auth/diary'
    assert client.get(path,params={'day':'2026-09-10'},headers=headers).json()['entries']==[]
    body={'day':'2026-09-10','period':'morning','food_id':'demo-chicken-can','grams':50}
    result=client.post(path,json=body,headers=headers)
    assert result.status_code==201
    assert result.json()['totals']=={'kcal':50,'protein':5,'fat':3,'carbs':.75}
    entry=result.json()['entries'][0]['id']
    assert client.get(path,params={'day':body['day']},headers=headers).json()['totals']['kcal']==50
    assert client.get(path,params={'day':'2026-09-11'},headers=headers).json()['entries']==[]
    other=verified(client,'other@example.com')
    assert client.get(path,params={'day':body['day']},headers=other).json()['entries']==[]
    assert client.post(f'{path}/{entry}/remove',headers=other).status_code==404
    result=client.post(f'{path}/{entry}/remove',headers=headers)
    assert result.json()['totals']['kcal']==0


@pytest.mark.parametrize('change',[{'grams':0},{'grams':-1},{'grams':1001},{'grams':'NaN'},{'grams':'Infinity'},{'grams':'abc'},{'period':'breakfast'},{'food_id':'other'},{'day':'2026-02-30'},{'cat_id':999}])
def test_diary_rejects_invalid_input(client,change):
    headers=verified(client)
    body={'day':'2026-09-10','period':'morning','food_id':'demo-chicken-can','grams':100,**change}
    assert client.post('/api/auth/diary',json=body,headers=headers).status_code==422


def test_diary_requires_verified_account(client):
    assert client.get('/api/auth/diary?day=2026-09-10').status_code==401
    payload=copy.deepcopy(ACCOUNT)
    result=client.post('/api/auth/register',json=payload)
    headers={'Authorization':'Bearer '+result.json()['access_token']}
    assert client.get('/api/auth/diary?day=2026-09-10',headers=headers).status_code==403
