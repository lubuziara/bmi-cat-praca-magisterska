import copy
import re
import time
from datetime import date, timedelta
from pathlib import Path
from email import policy
from email.parser import BytesParser
import pytest
from sqlalchemy import func, select
from app.database.models.cat import Cat
from app.database.models.owner_profile import OwnerProfile
from app.database.models.user import User
from app.database.models.verification_challenge import VerificationChallenge

ACCOUNT = {"first_name":"Anna","last_name":"Kowalska","gender":"female","birth_date":"1995-03-04",
           "phone":"+48 123 456 789","email":"anna@example.com","password":"Haslo bardzo dlugie!",
           "cat":{"name":"Mruczek","gender":"unknown","estimated_age_months":8}}


def register(client):
    response=client.post("/api/auth/register",json=copy.deepcopy(ACCOUNT))
    assert response.status_code==201
    return {"Authorization":"Bearer "+response.json()["access_token"]}


def read_code(client, channel):
    if channel=="phone":
        p=max(Path(client.app.state.settings.sms_outbox_dir).glob("*.txt"),key=lambda p:p.stat().st_mtime_ns)
        text=p.read_text(encoding="utf-8")
    else:
        p=max(Path(client.app.state.settings.outbox_dir).glob("verify-*.eml"),key=lambda p:p.stat().st_mtime_ns)
        text=BytesParser(policy=policy.default).parsebytes(p.read_bytes()).get_content()
    return re.search(r"\b([0-9]{6})\b",text).group(1)


def test_registration_saves_owner_cat_and_default_avatar(client):
    headers=register(client)
    with client.app.state.database.sessions() as db:
        profile=db.scalar(select(OwnerProfile));cat=db.scalar(select(Cat))
        assert profile.last_name=="Kowalska" and profile.phone=="+48123456789"
        assert cat.owner_id==profile.user_id
        assert cat.estimated_age_months==8 and cat.birth_date is None
        assert cat.age_recorded_on==date.today()
        assert cat.avatar=={"schema_version":1,"fur":"short","coat":"white","eyes":"green","size":"adult","body":"medium"}
    assert client.get("/api/auth/profile",headers=headers).status_code==403
    assert client.get("/api/auth/me",headers=headers).json()["registration_verified"] is False


def test_development_registration_happy_path_to_login_and_logout(client):
    assert client.get("/docs").status_code == 200
    created = client.post("/api/auth/register", json=ACCOUNT)
    assert created.status_code == 201 and created.json()["access_token"]
    headers = {"Authorization": "Bearer " + created.json()["access_token"]}
    for channel in ("email", "phone"):
        sent = client.post("/api/auth/verification/send", headers=headers, json={"channel": channel})
        assert sent.status_code == 200
        verified = client.post("/api/auth/verification/confirm", headers=headers,
                               json={"channel": channel, "code": read_code(client, channel)})
        assert verified.status_code == 200
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200 and me.json()["registration_verified"] is True
    assert client.get("/api/auth/profile", headers=headers).json()["cat"]["name"] == "Mruczek"
    login = client.post("/api/auth/login", json={"email": ACCOUNT["email"], "password": ACCOUNT["password"]})
    login_headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert login.status_code == 200 and client.post("/api/auth/logout", headers=login_headers).status_code == 200
    assert client.get("/api/auth/me", headers=login_headers).status_code == 401


def test_duplicate_registration_rolls_back_profile_and_cat(client):
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 201
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 409
    with client.app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1
        assert db.scalar(select(func.count()).select_from(OwnerProfile)) == 1
        assert db.scalar(select(func.count()).select_from(Cat)) == 1


@pytest.mark.parametrize("field,value",[("last_name","666"),("phone","123"),("phone","+000000000"),("gender","unexpected"),("birth_date","2050-01-01"),("birth_date","1999-02-30")])
def test_invalid_owner_data_rejected(client,field,value):
    payload=copy.deepcopy(ACCOUNT);payload[field]=value
    assert client.post("/api/auth/register",json=payload).status_code==422


@pytest.mark.parametrize("update",[
    {"name":"666"},{"birth_date":"2050-01-01","estimated_age_months":None},
    {"birth_date":None,"estimated_age_months":None},{"birth_date":"2024-01-01","estimated_age_months":2},
    {"estimated_age_months":-1},{"estimated_age_months":481},{"estimated_age_months":1.5},
    {"gender":"alien"},{"avatar":{"body":"unknown"}}, {"avatar":{"coat":"injected"}},
])
def test_invalid_cat_data_rejected(client,update):
    payload=copy.deepcopy(ACCOUNT);payload["cat"].update(update)
    assert client.post("/api/auth/register",json=payload).status_code==422


def test_exact_birthday_and_custom_avatar_persist(client):
    payload=copy.deepcopy(ACCOUNT)
    payload["cat"]={"name":"Luna","gender":"female","birth_date":"2025-02-01",
                    "avatar":{"fur":"extra_long","coat":"purple","eyes":"pink","size":"kitten","body":"slim"}}
    assert client.post("/api/auth/register",json=payload).status_code==201
    with client.app.state.database.sessions() as db:
        cat=db.scalar(select(Cat))
        assert cat.birth_date==date(2025,2,1) and cat.estimated_age_months is None
        assert cat.avatar["coat"]=="purple" and cat.avatar["body"]=="slim"


def test_both_channels_required_and_codes_are_single_use(client):
    headers=register(client)
    for channel in ["email","phone"]:
        sent=client.post("/api/auth/verification/send",headers=headers,json={"channel":channel})
        assert sent.status_code==200
        code=read_code(client,channel)
        assert code not in sent.text
        with client.app.state.database.sessions() as db:
            challenge=db.scalar(select(VerificationChallenge).where(VerificationChallenge.channel==channel))
            assert challenge.code_hash.startswith("$argon2id$") and code not in challenge.code_hash
        verified=client.post("/api/auth/verification/confirm",headers=headers,json={"channel":channel,"code":code})
        assert verified.status_code==200
        assert verified.json()["registration_verified"] is (channel=="phone")
        assert client.post("/api/auth/verification/confirm",headers=headers,json={"channel":channel,"code":code}).status_code==400
        if channel=="email":
            assert client.get("/api/auth/profile",headers=headers).status_code==403
    profile=client.get("/api/auth/profile",headers=headers)
    assert profile.status_code==200 and profile.json()["cat"]["name"]=="Mruczek"
    assert client.get("/api/auth/me",headers=headers).json()["registration_verified"] is True


def test_code_attempts_expiration_and_resend_limit(client):
    headers=register(client)
    client.post("/api/auth/verification/send",headers=headers,json={"channel":"phone"})
    code=read_code(client,"phone")
    assert client.post("/api/auth/verification/send",headers=headers,json={"channel":"phone"}).status_code==429
    wrong="000000" if code!="000000" else "111111"
    for _ in range(5):
        assert client.post("/api/auth/verification/confirm",headers=headers,json={"channel":"phone","code":wrong}).status_code==400
    assert client.post("/api/auth/verification/confirm",headers=headers,json={"channel":"phone","code":code}).status_code==429
    with client.app.state.database.sessions() as db:
        challenge=db.scalar(select(VerificationChallenge));challenge.expires_at=int(time.time())-1;db.commit()
    assert client.post("/api/auth/verification/confirm",headers=headers,json={"channel":"phone","code":code}).status_code==400


def test_verification_requires_session_and_other_user_cannot_use_code(client):
    assert client.post("/api/auth/verification/send",json={"channel":"phone"}).status_code==401
    headers=register(client)
    client.post("/api/auth/verification/send",headers=headers,json={"channel":"phone"})
    code=read_code(client,"phone")
    payload=copy.deepcopy(ACCOUNT);payload["email"]="second@example.com"
    second=client.post("/api/auth/register",json=payload).json()["access_token"]
    assert client.post("/api/auth/verification/confirm",headers={"Authorization":"Bearer "+second},json={"channel":"phone","code":code}).status_code==400
