import pytest
from planning.sip import calculate_sip
from planning.emi import calculate_emi
from planning.insights import generate_planning_insight
import json

def test_sip_normal():
    res = calculate_sip(10000, 12, 1)
    assert res['total_invested'] == 120000
    assert res['future_value'] > 120000
    assert len(res['yearly_breakdown']) == 1

def test_sip_zero_interest():
    res = calculate_sip(10000, 0, 1)
    assert res['total_invested'] == 120000
    assert res['future_value'] == 120000
    assert res['est_returns'] == 0

def test_sip_invalid():
    res = calculate_sip(-100, 12, 1)
    assert res['total_invested'] == 0
    assert res['future_value'] == 0

def test_emi_normal():
    res = calculate_emi(100000, 12, 1)
    assert res['monthly_emi'] > 0
    assert res['total_interest'] > 0
    assert res['total_payment'] > 100000
    assert len(res['yearly_amortization']) == 1

def test_emi_zero_interest():
    res = calculate_emi(120000, 0, 1)
    assert res['monthly_emi'] == 10000
    assert res['total_interest'] == 0
    assert res['total_payment'] == 120000

def test_emi_invalid():
    res = calculate_emi(-100, 12, 1)
    assert res['monthly_emi'] == 0

def test_insights():
    # 20% -> SUCCESS
    res1 = generate_planning_insight(2000, 10000, "SIP")
    assert res1['status'] == 'SUCCESS'
    
    # 85% -> WARNING
    res2 = generate_planning_insight(8500, 10000, "EMI")
    assert res2['status'] == 'WARNING'
    assert '85%' in res2['message']
    
    # > 100% -> WARNING
    res3 = generate_planning_insight(12000, 10000, "EMI")
    assert res3['status'] == 'WARNING'
    assert 'exceeds' in res3['message']

@pytest.fixture
def auth_client(client, app):
    client.post('/api/auth/register', json={
        "username": "planuser",
        "email": "planuser@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })
    response = client.post('/api/auth/login', json={
        "username": "planuser",
        "password": "Password123!"
    })
    
    csrf_token = None
    for header in response.headers.getlist('Set-Cookie'):
        if 'csrf_access_token=' in header:
            csrf_token = header.split('csrf_access_token=')[1].split(';')[0]
            break
            
    client.csrf_token = csrf_token
    yield client

def test_api_capacity(auth_client, monkeypatch):
    from utils.rule_engine import FinancialPeriod
    
    # Mock build_financial_periods
    def mock_build(user_id, months):
        return [FinancialPeriod("2023-10", 50000, 0, [])]
        
    monkeypatch.setattr('routes.planning.build_financial_periods', mock_build)
    
    res = auth_client.get('/app/api/planning/capacity', headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['savings'] == 50000
    assert data['suggested_sip_min'] == 15000

def test_api_sip(auth_client):
    payload = {
        "monthly_investment": 10000,
        "annual_rate": 12,
        "years": 10
    }
    res = auth_client.post('/app/api/planning/calculate_sip', json=payload, headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'future_value' in data
    assert 'yearly_breakdown' in data

def test_api_emi_vehicle(auth_client):
    payload = {
        "principal": 0,
        "loan_type": "Car",
        "vehicle_price": 1000000,
        "down_payment": 200000,
        "annual_rate": 8.5,
        "years": 5
    }
    res = auth_client.post('/app/api/planning/calculate_emi', json=payload, headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'monthly_emi' in data
    assert data['total_payment'] > 800000
