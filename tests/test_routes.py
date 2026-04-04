def test_health_returns_json(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.is_json
    assert res.get_json() == {"status": "healthy"}


def test_root_redirects_to_login_when_anonymous(client):
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert res.location.endswith("/login")


def test_login_success_sets_session_and_redirects(client):
    res = client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "/dashboard" in res.location


def test_login_failure_renders_error(client):
    res = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Invalid credentials" in res.data


def test_dashboard_requires_login(client):
    res = client.get("/dashboard", follow_redirects=False)
    assert res.status_code == 302
    assert "/login" in res.location


def test_dashboard_ok_when_logged_in(logged_in_client):
    res = logged_in_client.get("/dashboard")
    assert res.status_code == 200
    assert b"admin" in res.data


def test_clients_requires_login(client):
    res = client.get("/clients", follow_redirects=False)
    assert res.status_code == 302


def test_add_client_then_listed(logged_in_client):
    res = logged_in_client.post(
        "/clients",
        data={"_action": "add", "name": "Test Client"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Test Client" in res.data


def test_duplicate_client_flash(logged_in_client):
    logged_in_client.post(
        "/clients",
        data={"_action": "add", "name": "Dup"},
        follow_redirects=True,
    )
    res = logged_in_client.post(
        "/clients",
        data={"_action": "add", "name": "Dup"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"already exists" in res.data


def test_client_summary_requires_selection(logged_in_client):
    res = logged_in_client.get("/client/summary", follow_redirects=True)
    assert res.status_code == 200
    assert b"Select a client first" in res.data


def test_select_client_then_summary(logged_in_client):
    logged_in_client.post(
        "/clients",
        data={"_action": "add", "name": "Pat"},
        follow_redirects=True,
    )
    logged_in_client.post(
        "/clients",
        data={"_action": "select", "name": "Pat"},
        follow_redirects=True,
    )
    res = logged_in_client.get("/client/summary")
    assert res.status_code == 200
    assert b"Pat" in res.data
    assert b"Program:" in res.data


def test_logout_clears_session(logged_in_client):
    logged_in_client.get("/logout", follow_redirects=True)
    res = logged_in_client.get("/dashboard", follow_redirects=False)
    assert res.status_code == 302
    assert "/login" in res.location
