"""Cron endpoints are only callable with the shared CRON_SECRET."""
import pytest

from tests.conftest import TEST_CRON_SECRET

URL = '/api/cron/event-deadlines/'


@pytest.fixture
def job_calls(monkeypatch):
    from app.routes import cron_routes
    calls = []
    monkeypatch.setattr(cron_routes, 'run_event_deadlines', lambda: calls.append(1) or {'processed': 0})
    return calls


@pytest.mark.parametrize('headers', [{}, {'Authorization': 'Bearer wrong'}, {'Authorization': TEST_CRON_SECRET}])
def test_rejects_missing_or_wrong_secret(client, job_calls, headers):
    assert client.post(URL, headers=headers).status_code == 401
    assert job_calls == []


def test_runs_job_with_secret(client, job_calls):
    res = client.post(URL, headers={'Authorization': f'Bearer {TEST_CRON_SECRET}'})
    assert res.status_code == 200 and res.get_json()['success'] is True
    assert job_calls == [1]


def test_refuses_everything_when_secret_unset(client, app, job_calls):
    app.config['CRON_SECRET'] = None
    assert client.post(URL, headers={'Authorization': f'Bearer {TEST_CRON_SECRET}'}).status_code == 500
    assert job_calls == []
