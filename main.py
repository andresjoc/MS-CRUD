from fastapi import FastAPI
from routes import country
from routes import region
from routes import city
from routes import app_user
from routes import health_record
from routes import history
from routes import wearable_model
from routes import wearable
from routes import monitoring_session
from routes import measurement
from routes import metric_type
from routes import alert
from routes import severity_level
from routes import ppg_sample
from routes import compute_status

from fastapi.middleware.cors import CORSMiddleware
from config.environment import CORS_ORIGINS

app = FastAPI(title="Ppg-monitoring-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"message": "HeartSense MSCRUD is running"}

app.include_router(alert.router)
app.include_router(app_user.router)
app.include_router(city.router)
app.include_router(compute_status.router)
app.include_router(country.router)
app.include_router(region.router)
app.include_router(health_record.router)
app.include_router(history.router)
app.include_router(measurement.router)
app.include_router(metric_type.router)
app.include_router(monitoring_session.router)
app.include_router(ppg_sample.router)
app.include_router(severity_level.router)
app.include_router(wearable.router)
app.include_router(wearable_model.router)
