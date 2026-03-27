import os
import requests

API_URL = os.getenv("API_GATEWAY_URL", "http://localhost:9000")


class APIClient:
    def __init__(self, token: str | None = None):
        self.base = API_URL
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def _get(self, path: str, params: dict | None = None) -> dict | list | None:
        try:
            r = requests.get(f"{self.base}{path}", headers=self.headers, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _post(self, path: str, body: dict) -> dict | None:
        try:
            r = requests.post(f"{self.base}{path}", json=body, headers=self.headers, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _patch(self, path: str, body: dict | None = None) -> dict | None:
        try:
            r = requests.patch(f"{self.base}{path}", json=body or {}, headers=self.headers, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None


    def register(self, email: str, password: str, full_name: str) -> dict | None:
        return self._post("/auth/register", {"email": email, "password": password, "full_name": full_name})

    def login(self, email: str, password: str) -> dict | None:
        return self._post("/auth/login", {"email": email, "password": password})

    def me(self) -> dict | None:
        return self._get("/auth/me")


    def list_accounts(self) -> list:
        return self._get("/accounts") or []

    def create_account(self, name: str, currency: str) -> dict | None:
        return self._post("/accounts", {"name": name, "currency": currency})


    def list_transactions(self, account_id: str | None = None) -> list:
        params = {"account_id": account_id} if account_id else None
        return self._get("/transactions", params=params) or []

    def create_transaction(self, account_id: str, amount: float, tx_type: str, description: str, category: str) -> dict | None:
        return self._post("/transactions", {
            "account_id": account_id,
            "amount": amount,
            "type": tx_type,
            "description": description,
            "category": category,
        })

    def monthly_summary(self, account_id: str | None = None) -> dict | None:
        params = {"account_id": account_id} if account_id else None
        return self._get("/transactions/summary/monthly", params=params)


    def evaluate_risk(self, entity_id: str, entity_type: str = "account") -> dict | None:
        return self._post("/risk/scores", {"entity_id": entity_id, "entity_type": entity_type})

    def get_risk_score(self, entity_id: str) -> dict | None:
        return self._get(f"/risk/scores/{entity_id}")

    def list_alerts(self) -> list:
        return self._get("/risk/alerts") or []

    def resolve_alert(self, alert_id: str) -> dict | None:
        return self._patch(f"/risk/alerts/{alert_id}/resolve")


    def create_session(self, title: str = "Dashboard session") -> dict | None:
        return self._post("/agents/sessions", {"title": title})

    def run_agent(self, session_id: str, message: str) -> dict | None:
        return self._post("/agents/runs", {"session_id": session_id, "user_message": message})


    def list_reports(self) -> list:
        return self._get("/reporting/reports") or []

    def create_report(self, report_type: str, account_id: str | None = None, title: str | None = None) -> dict | None:
        body: dict = {"report_type": report_type}
        if account_id:
            body["account_id"] = account_id
        if title:
            body["title"] = title
        return self._post("/reporting/reports", body)

    def get_report(self, report_id: str) -> dict | None:
        return self._get(f"/reporting/reports/{report_id}")
