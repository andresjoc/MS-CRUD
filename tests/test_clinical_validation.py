from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from main import app
from tests.test_auth_guard import make_token

client = TestClient(app)


def test_batch_upload_requires_authentication():
    response = client.post(
        "/clinical_validation/batch_upload",
        json={"records": [{"id": "rec-unauth-1"}]}
    )
    assert response.status_code == 401


def test_batch_upload_successful_with_full_ppg_signal():
    token = make_token(user_id=1, email="a@h.com")
    headers = {"Authorization": f"Bearer {token}"}

    sample_signal = [
        {"t": round(i * 0.04, 2), "v": round(0.5 + 0.1 * (i % 25), 4)}
        for i in range(1500)
    ]

    record_payload = {
        "id": "rec-pytest-001",
        "patientCode": "HS-AF-999",
        "captureIndex": 1,
        "cohort": "AF",
        "age": 68,
        "biologicalSex": "Masculino",
        "weightKg": 78.5,
        "heightCm": 172.0,
        "skinTemperature": 33.4,
        "fitzpatrickScale": 3,
        "wrist": "Izquierda",
        "hasAfHistory": True,
        "afSubtype": "Permanente",
        "timeSinceDiagnosis": "3 años",
        "comorbidities": ["HTA", "Insuficiencia Cardíaca"],
        "cardioDrugs12h": ["Metoprolol 50mg"],
        "deviceHistory": ["Ninguno"],
        "observations": "Prueba automatizada pytest",
        "ecgRhythmDiagnosis": "Fibrilación Auricular",
        "ecgModality": "Telemetría",
        "evaluatingPhysician": "Dr. Pytest",
        "ecgTakenAt": datetime.now(timezone.utc).isoformat(),
        "aiAfDetected": True,
        "aiConfidence": 0.965,
        "heartRateBpm": 84.5,
        "hrvRmssd": 72.3,
        "hrvSdnn": 68.1,
        "isTachycardic": False,
        "recordedBeatsCount": 82,
        "recordingDurationSeconds": 60,
        "rawPpgData": {
            "samplingRateHz": 25,
            "samplesCount": len(sample_signal),
            "samples": sample_signal
        },
        "syncStatus": "PENDING"
    }

    response = client.post(
        "/clinical_validation/batch_upload",
        json={"records": [record_payload]},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["synced_count"] == 1
    assert "rec-pytest-001" in data["synced_ids"]
    assert data["evaluator_user_id"] == 1


def test_batch_upload_is_idempotent():
    token = make_token(user_id=1, email="a@h.com")
    headers = {"Authorization": f"Bearer {token}"}

    record_payload = {
        "id": "rec-pytest-001",
        "patientCode": "HS-AF-999",
        "captureIndex": 1,
        "cohort": "AF",
        "age": 68,
        "biologicalSex": "Masculino",
        "weightKg": 78.5,
        "heightCm": 172.0,
        "skinTemperature": 33.4,
        "fitzpatrickScale": 3,
        "wrist": "Izquierda",
        "hasAfHistory": True,
        "ecgRhythmDiagnosis": "Fibrilación Auricular (Confirmada)",
        "ecgModality": "ECG 12 Derivaciones",
        "evaluatingPhysician": "Dr. Pytest Actualizado",
        "aiAfDetected": True,
        "aiConfidence": 0.98,
        "heartRateBpm": 85.0,
        "hrvRmssd": 75.0,
    }

    response = client.post(
        "/clinical_validation/batch_upload",
        json={"records": [record_payload]},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["synced_count"] == 1


def test_list_clinical_records_filtering():
    token = make_token(user_id=1, email="a@h.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/clinical_validation/records?cohort=AF",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    codes = [r["patient_code"] for r in data["records"]]
    assert "HS-AF-999" in codes
