# 🗄️ Auricular Sense - MS CRUD (PPG Monitoring Storage API)

Microservicio central de persistencia y exposición de datos para el ecosistema **Auricular Sense**. Responsable del almacenamiento, consulta y control de acceso basado en roles/propietario para usuarios, dispositivos *wearables*, sesiones de monitoreo, muestras biomédicas PPG, métricas fisiológicas y alertas cardíacas.

---

## 📋 Responsabilidades y Dominio

- **Persistencia de Dominio:** Gestión de tablas relacionales de usuarios (`app_user`), antropometría (`health_record`), catálogo geográfico (`country`, `region`, `city`), dispositivos (`wearable`, `wearable_model`) y eventos de salud.
- **Ingesta de Datos Biomédicos de Alta Escala:**
  - Ingesta en lote de sesiones completas (`POST /monitoring_sessions/batch`) proveniente de la cola offline de la app móvil.
  - Almacenamiento optimizado de series temporales de muestras fotopletismográficas (`ppg_sample`).
- **Historial Consolidado:** Endpoint unificado (`GET /history/`) para que la app reconstruya el historial tras reinstalación o inicio de sesión.
- **Protocolo de Validación Clínica:** Endpoints dedicados (`/clinical_validation/`) para el protocolo de investigación hospitalaria con trazabilidad de ECG patrón de oro.
- **Control de Acceso por Propietario (JWT):** Valida localmente el token emitido por `ms-auth`. Un usuario **solo puede leer o modificar sus propios datos**. Cualquier intento de acceder a recursos ajenos responde `403 Forbidden`.

> [!IMPORTANT]
> `ms-crud` **no autentica usuarios ni almacena contraseñas**. No accede a `auth_credential`. La identidad se extrae y valida de forma estricta desde el claim `sub` del Bearer JWT emitido por `ms-auth`.

---

## 🏛️ Modelo de Datos y Jerarquías

```mermaid
erDiagram
    APP_USER ||--o{ WEARABLE : "posee"
    APP_USER ||--o{ MONITORING_SESSION : "registra"
    WEARABLE ||--o{ MONITORING_SESSION : "capturada con"
    MONITORING_SESSION ||--o{ MEASUREMENT : "contiene metricas"
    MONITORING_SESSION ||--o{ PPG_SAMPLE : "contiene senal cruda"
    MONITORING_SESSION ||--o{ ALERT : "genera"

    MONITORING_SESSION {
        int id_session PK
        int id_user FK
        int id_wearable FK
        datetime start_time
        datetime end_time
        string status
    }

    MEASUREMENT {
        int id_measurement PK
        int id_session FK
        int id_metric_type FK
        decimal value
        datetime timestamp
    }

    PPG_SAMPLE {
        bigint id_sample PK
        int id_session FK
        datetime timestamp
        int green_value
        int red_value
        int ir_value
    }
```

---

## ⚙️ Prerrequisitos de Entorno

- **Python:** Versión `3.10` o superior (compatible con Python 3.11, 3.12 y 3.13).
- **Base de Datos:** Instancia de **PostgreSQL 14+** (local) o **Neon Serverless PostgreSQL**. Compatible opcionalmente con **TimescaleDB** para compresión de hipertablas en `ppg_sample`.
- **Esquema Inicial:** Base de datos creada con las tablas de `BD/ppg-database-design/sql/`.

---

## 🚀 Guía de Instalación y Replicación Paso a Paso

### 1. Clonar y Acceder al Directorio

```bash
git clone https://github.com/andresjoc/MS-CRUD.git
cd MS-CRUD
```

### 2. Crear y Activar el Entorno Virtual

En **Windows (PowerShell)**:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

En **Linux / macOS**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copia el archivo de plantilla `.env.example` a `.env`:

En **Windows (PowerShell)**:
```powershell
Copy-Item .env.example .env
```

En **Linux / macOS**:
```bash
cp .env.example .env
```

Configura los parámetros en `.env`:

```env
# Cadena de conexión a PostgreSQL (misma base o esquema compartido con ms-auth)
DATABASE_URL=postgresql://usuario:password@localhost:5432/PPG_DB

# Clave y algoritmo simétrico idénticos a los configurados en ms-auth
JWT_SECRET_KEY=clave-secreta-super-segura-y-larga-para-produccion
JWT_ALGORITHM=HS256
```

---

## 🧪 Suite de Pruebas Automatizadas

El microservicio cuenta con pruebas automáticas con base de datos SQLite en memoria:

```bash
python -m pytest tests/
```

Salida esperada:
```text
======================= 13 passed in 5.33s =======================
```

Las pruebas cubren:
* Validación estricta del guardia JWT (`dependencies/auth_guard.py`).
* Control de acceso y aislamiento por propietario (`tests/test_crud_api.py`).
* Idempotencia y transaccionalidad de subidas en lote (`tests/test_clinical_validation.py`).

---

## 🏃 Ejecución del Microservicio

Con el entorno virtual activo:

```bash
uvicorn main:app --reload --port 8000
```

El servicio iniciará en:
* **API Base:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Documentación Interactiva (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Documentación Alternativa (ReDoc):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 Endpoints Clave del Sistema

### 1. Ingesta de Sesión Completa en Lote (`POST /monitoring_sessions/batch`)
Utilizado por la cola offline de la aplicación Flutter (`OfflineSyncQueueManager`). Permite subir en una única transacción atómica:
* La sesión de monitoreo (`monitoring_session`).
* Las métricas calculadas (FC, SpO2, HRV RMSSD, etc. en `measurement`).
* El vector completo de muestras de señal fotopletismográfica (`ppg_sample`).
* Alertas de fibrilación auricular o taquicardia generadas en el dispositivo (`alert`).

**Header Requerido:**
```http
Authorization: Bearer <JWT_DE_MS_AUTH>
```

**Payload:**
```json
{
  "id_wearable": 1,
  "start_time": "2026-11-07T14:30:00Z",
  "end_time": "2026-11-07T14:31:00Z",
  "measurements": [
    { "id_metric_type": 1, "value": 72.0, "timestamp": "2026-11-07T14:30:30Z" },
    { "id_metric_type": 2, "value": 98.0, "timestamp": "2026-11-07T14:30:30Z" },
    { "id_metric_type": 3, "value": 42.5, "timestamp": "2026-11-07T14:30:30Z" }
  ],
  "samples": [
    { "timestamp": "2026-11-07T14:30:00.000Z", "green_value": 2048, "red_value": 0, "ir_value": 0 }
  ],
  "alert": {
    "id_severity": 1,
    "message": "Ritmo sinusal normal",
    "timestamp": "2026-11-07T14:31:00Z"
  }
}
```

---

### 2. Historial Paginado del Usuario (`GET /history/`)
Devuelve el listado consolidado de mediciones del usuario autenticado para visualización en pantalla o generación de reportes clínicos PDF.

```bash
curl -X GET "http://127.0.0.1:8000/history/?limit=50&offset=0" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

---

### 3. Registro y Consulta de Wearables (`/wearables`)
Permite vincular relojes inteligentes (**PineTime** o **Samsung Galaxy Watch**) a la cuenta del usuario:

* `GET /wearables`: Lista los dispositivos vinculados al usuario autenticado.
* `POST /wearables`: Registra un nuevo dispositivo asociándolo al `id_user` del token.

---

### 4. Protocolo de Validación Clínica (`/clinical_validation/`)
Módulo especializado para la validación médica hospitalaria (70 pacientes):
* `POST /clinical_validation/batch_upload`: Ingesta masiva idempotente de fichas clínicas con diagnóstico médico ECG.
* `GET /clinical_validation/records`: Consulta y exportación de registros clínicos.

---

## 🔒 Matriz de Seguridad y Reglas de Acceso

| Recurso | Nivel de Acceso | Regla de Autorización |
| :--- | :--- | :--- |
| `/countries`, `/regions`, `/cities` | Público | Catálogo abierto para formularios de registro. |
| `/wearable-models`, `/metric-types` | Público | Metadatos de dispositivos y métricas. |
| `/App_users/{id_user}` | Protegido (JWT) | Solo permite consultar o modificar el propio perfil. |
| `/wearables/**` | Protegido (JWT) | Solo permite manipular dispositivos propios. |
| `/monitoring_sessions/**` | Protegido (JWT) | Solo permite acceder a sesiones propias. |
| `/Measurements/**`, `/ppg_samples/**` | Protegido (JWT) | Validado contra la propiedad de la sesión asociada. |
| `/history/` | Protegido (JWT) | Filtra automáticamente por `id_user` del token. |

Cualquier solicitud con token expirado, firma alterada o sin header responderá `401 Unauthorized`. Si el recurso solicitado existe pero pertenece a otro usuario, responderá `403 Forbidden`.
