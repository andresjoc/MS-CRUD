# Documentación Técnica del Proyecto

## 1. Descripción general

Este proyecto es una API REST construida con **FastAPI** para gestionar un sistema de monitoreo **PPG (Photoplethysmography)**. El objetivo de la API es centralizar la información relacionada con:

- usuarios de la aplicación,
- ubicación geográfica,
- historial de salud,
- dispositivos wearables,
- sesiones de monitoreo,
- muestras PPG,
- mediciones derivadas,
- alertas clínicas o técnicas,
- estados de procesamiento.

La API sigue una estructura por capas relativamente simple:

- **Capa de entrada HTTP**: rutas FastAPI.
- **Capa de validación/serialización**: esquemas Pydantic.
- **Capa de persistencia**: modelos SQLAlchemy.
- **Capa de utilidades de consulta**: filtrado, ordenamiento y paginación.
- **Capa de configuración**: variables de entorno y conexión a base de datos.

La base de datos esperada es **PostgreSQL**.

---

## 2. Estructura del proyecto

```text
ppg-monitoring-api/
├── main.py
├── README.md
├── requeriment.txt
├── .env
├── .env.example
├── config/
│   └── environment.py
├── DAO/
│   └── database.py
├── DTO/
│   └── models.py
├── ORM/
│   └── schemas.py
├── routes/
│   ├── alert.py
│   ├── app_user.py
│   ├── city.py
│   ├── compute_status.py
│   ├── country.py
│   ├── health_record.py
│   ├── measurement.py
│   ├── metric_type.py
│   ├── monitoring_session.py
│   ├── ppg_sample.py
│   ├── severity_level.py
│   ├── wearable.py
│   └── wearable_model.py
└── utils/
    └── query_builder.py
```

---

## 3. Rol de cada carpeta y archivo

### `main.py`

Es el punto de entrada de la aplicación. Aquí se crea la instancia de `FastAPI` y se registran todos los routers del sistema.

Responsabilidades:

- inicializar la API,
- asignar el título del servicio,
- montar todos los endpoints por módulo.

En otras palabras, `main.py` no contiene lógica de negocio; solo compone la aplicación.

### `config/environment.py`

Carga variables de entorno usando `python-dotenv` y expone `DATABASE_URL`.

Responsabilidades:

- leer la configuración desde `.env`,
- proveer una URL por defecto para PostgreSQL si no existe variable definida.

Valor por defecto actual:

```env
postgresql://postgres:postgres@localhost:5432/PPG_DB
```

### `DAO/database.py`

Define la conexión a la base de datos y la sesión de SQLAlchemy.

Responsabilidades:

- crear `engine`,
- crear `SessionLocal`,
- declarar `Base` para los modelos,
- exponer `get_db()` como dependencia de FastAPI para inyectar sesiones en cada endpoint.

`get_db()` abre una sesión por request y la cierra al terminar.

### `DTO/models.py`

Aunque la carpeta se llama `DTO`, este archivo realmente contiene los **modelos ORM de SQLAlchemy**, es decir, el mapeo de tablas de base de datos.

Responsabilidades:

- definir tablas,
- definir columnas,
- definir claves foráneas,
- definir relaciones entre entidades.

Este es el núcleo de persistencia del proyecto.

### `ORM/schemas.py`

Aunque la carpeta se llama `ORM`, este archivo contiene los **schemas Pydantic**, usados para:

- validar datos de entrada,
- definir la forma de las respuestas,
- separar modelos de transporte respecto a los modelos de base de datos.

Hay dos patrones principales:

- `XCreate`: para creación/actualización,
- `XResponse`: para respuestas serializadas.

### `routes/`

Contiene un archivo por agregado o entidad de negocio. Cada módulo expone endpoints REST para operaciones CRUD y, en algunos casos, consultas específicas por relación.

### `utils/query_builder.py`

Implementa una capa reusable para enriquecer los `GET` con:

- filtros dinámicos,
- operadores de comparación,
- filtros anidados por relaciones,
- ordenamiento,
- paginación.

Es uno de los componentes más útiles del proyecto, porque evita duplicar lógica de consulta en cada ruta.

### `requeriment.txt`

Lista de dependencias Python del proyecto:

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `psycopg2-binary`
- `pydantic[email]`
- `python-dotenv`

---

## 4. Arquitectura funcional

El flujo típico de una solicitud es este:

1. El cliente hace una petición HTTP a un endpoint.
2. FastAPI la enruta al archivo correspondiente dentro de `routes/`.
3. El esquema Pydantic valida el payload.
4. Se obtiene una sesión de base de datos con `Depends(get_db)`.
5. Se consulta o modifica la base a través de los modelos SQLAlchemy.
6. El resultado se serializa con un `Response schema`.
7. Se devuelve la respuesta HTTP.

### Flujo resumido

```mermaid
flowchart LR
    A["Cliente HTTP"] --> B["Ruta FastAPI"]
    B --> C["Schema Pydantic"]
    B --> D["Session DB"]
    D --> E["Modelos SQLAlchemy"]
    E --> F["PostgreSQL"]
    E --> G["Respuesta serializada"]
    C --> G
    G --> A
```

### Historial consolidado para la app

Ademas de los CRUD por entidad, el servicio expone `GET /history/` para que la app Flutter cargue el historial completo del usuario autenticado en una sola consulta logica.

Caracteristicas:

- requiere `Authorization: Bearer <jwt>`
- usa el `user_id` del token, no parametros enviados por el cliente
- soporta `limit` y `offset`
- devuelve sesiones ordenadas por fecha de creacion descendente
- incluye `compute_status`, mediciones, muestras PPG y alertas de cada sesion
- permite reconstruir historial despues de cerrar sesion y volver a entrar

La app elimina elementos de historial usando `DELETE /monitoring_sessions/{id_session}`. Esa ruta valida pertenencia del usuario y elimina los datos hijos por las relaciones configuradas en el modelo.

---

## 5. Modelo de dominio

El sistema gira alrededor de un usuario, su contexto geográfico, sus dispositivos y las sesiones de monitoreo fisiológico.

### Relación conceptual principal

```mermaid
erDiagram
    COUNTRY ||--o{ REGION : has
    REGION ||--o{ CITY : has
    CITY ||--o{ APP_USER : has
    APP_USER ||--o{ HEALTH_RECORD : has
    APP_USER ||--o{ WEARABLE : owns
    WEARABLE_MODEL ||--o{ WEARABLE : classifies
    APP_USER ||--o{ MONITORING_SESSION : starts
    COMPUTE_STATUS ||--o{ MONITORING_SESSION : labels
    MONITORING_SESSION ||--o{ MEASUREMENT : contains
    METRIC_TYPE ||--o{ MEASUREMENT : types
    MONITORING_SESSION ||--o{ ALERT : raises
    SEVERITY_LEVEL ||--o{ ALERT : classifies
    MONITORING_SESSION ||--o{ PPG_SAMPLE : stores
```

---

## 6. Entidades del sistema

### 6.1 `Country`

Representa un país.

Campos:

- `id_country`
- `name`

Uso:

- sirve como catálogo geográfico de nivel superior,
- se relaciona con ciudades.

### 6.2 `Region`

Representa una región asociada a un país.

Campos:

- `id_region`
- `id_country`
- `name`

Uso:

- nivel geográfico intermedio entre país y ciudad.

Relaciones:

- muchas regiones pertenecen a un país,
- una región puede tener muchas ciudades.

### 6.3 `City`

Representa una ciudad asociada a una región.

Campos:

- `id_city`
- `id_region`
- `name`

Uso:

- vincula usuarios con una ubicación.

Relaciones:

- muchas ciudades pertenecen a una región,
- una ciudad puede tener muchos usuarios.

### 6.4 `App_user`

Representa el usuario principal del sistema.

Campos:

- `id_user`
- `id_city`
- `email`
- `first_name`
- `last_name`
- `birth_date`
- `created_at`
- `updated_at`

Uso:

- es la entidad central del dominio,
- conecta salud, wearables y sesiones de monitoreo.

Relaciones:

- pertenece a una ciudad,
- tiene muchos registros de salud,
- tiene muchos wearables,
- tiene muchas sesiones de monitoreo.

### 6.5 `HealthRecord`

Representa un registro de salud del usuario.

Campos:

- `id_health_record`
- `id_user`
- `weight_kg`
- `height_cm`
- `recorded_at`

Uso:

- almacenar medidas biométricas históricas del usuario.

### 6.6 `WearableModel`

Representa el modelo comercial/técnico del dispositivo.

Campos:

- `id_wearable_model`
- `brand`
- `model`

Uso:

- separar el catálogo de modelos respecto a las unidades físicas concretas.

### 6.7 `Wearable`

Representa un dispositivo físico asignado a un usuario.

Campos:

- `id_wearable`
- `id_wearable_model`
- `id_user`
- `created_at`
- `updated_at`

Uso:

- identificar el hardware concreto que genera datos.

Relaciones:

- pertenece a un usuario,
- referencia un modelo de wearable.

### 6.8 `MonitoringSession`

Representa una sesión de monitoreo fisiológico.

Campos:

- `id_session`
- `id_user`
- `id_compute_status`
- `date_time`
- `created_at`
- `updated_at`
- `is_delta_encoded`

Uso:

- encapsular una captura o proceso de monitoreo,
- agrupar muestras PPG, métricas y alertas.

Relaciones:

- pertenece a un usuario,
- tiene un estado de cómputo,
- contiene mediciones,
- contiene alertas,
- contiene muestras PPG.

### 6.9 `MetricType`

Define el tipo de métrica que puede registrarse o derivarse.

Campos:

- `id_metric_type`
- `unit`
- `min_value`
- `max_value`
- `is_derived`
- `name`

Uso:

- describir métricas como frecuencia cardiaca, SpO2, HRV u otras.

### 6.10 `Measurement`

Representa una medición asociada a una sesión.

Campos:

- `id_measurement`
- `id_metric_type`
- `id_session`
- `value`
- `error_message`
- `recorded_at`

Uso:

- almacenar resultados numéricos producidos durante o después del procesamiento.

### 6.11 `SeverityLevel`

Catálogo de niveles de severidad.

Campos:

- `id_severity_level`
- `description`
- `name`

Uso:

- clasificar alertas por criticidad.

### 6.12 `Alert`

Representa una alerta generada sobre una sesión.

Campos:

- `id_alert`
- `id_session`
- `id_severity_level`
- `description`
- `created_at`
- `updated_at`

Uso:

- registrar eventos clínicos, anómalos o de procesamiento.

### 6.13 `ComputeStatus`

Representa el estado de procesamiento computacional de una sesión.

Campos:

- `id_compute_status`
- `name`
- `description`

Uso:

- modelar estados como pendiente, procesando, completado, fallido u otros equivalentes.

### 6.14 `PpgSample`

Representa una muestra cruda PPG.

Campos:

- `id_ppg_sample`
- `id_session`
- `ts`
- `green`
- `red`
- `ir`

Uso:

- almacenar señales crudas capturadas por el sensor,
- soportar análisis posterior,
- diferenciar canales ópticos verde, rojo e infrarrojo.

---

## 7. Esquemas Pydantic y validación

El archivo `ORM/schemas.py` define las estructuras de entrada y salida.

### Patrón usado

Para casi todas las entidades hay dos clases:

- `Create`: entrada para `POST` y `PUT`
- `Response`: salida para `GET` y respuestas CRUD

### Validaciones destacables

- `AppUserCreate.email` usa `EmailStr`.
- `AppUserCreate.password` entra como texto plano y luego se guarda directamente en `password_hash`.
- varios campos usan `Decimal` para preservar precisión en métricas.
- fechas y timestamps usan `date` y `datetime`.

### Observación importante

Aunque el campo de base de datos se llama `password_hash`, actualmente la API recibe `password` y lo almacena sin hashing. Eso implica que hoy el proyecto **no implementa un mecanismo real de protección de contraseñas**.

---

## 8. Endpoints y funcionalidades por módulo

## 8.1 Países - `/countries`

Funcionalidades:

- crear país,
- listar países,
- consultar país por ID,
- actualizar país,
- eliminar país.

Caso de uso:

- catálogo base para ciudades.

## 8.2 Ciudades - `/cities`

Funcionalidades:

- crear ciudad validando que el país exista,
- listar ciudades,
- consultar ciudad por ID,
- actualizar ciudad,
- eliminar ciudad.

Caso de uso:

- asignar ubicación a usuarios.

## 8.3 Usuarios - `/App_users`

Funcionalidades:

- crear usuario,
- validar email único al crear,
- listar usuarios,
- consultar usuario por ID,
- actualizar usuario,
- eliminar usuario.

Observaciones:

- no hay login,
- no hay autenticación,
- no hay hashing de contraseñas,
- la actualización no valida colisión de email con otro usuario.

## 8.4 Registros de salud - `/health-records`

Funcionalidades:

- crear registro verificando existencia de usuario,
- listar registros,
- consultar por ID,
- actualizar,
- eliminar.

Caso de uso:

- evolución antropométrica del usuario.

## 8.5 Modelos de wearable - `/wearable-models`

Funcionalidades:

- crear modelo,
- listar,
- consultar por ID,
- actualizar,
- eliminar.

Caso de uso:

- catálogo de marcas/modelos de hardware.

## 8.6 Wearables - `/wearables`

Funcionalidades:

- crear wearable validando usuario y modelo,
- listar wearables,
- listar wearables por usuario,
- consultar wearable por ID,
- actualizar wearable,
- eliminar wearable.

Caso de uso:

- asociar un dispositivo físico a un usuario concreto.

## 8.7 Sesiones de monitoreo - `/monitoring_sessions`

Funcionalidades:

- crear sesión validando usuario,
- listar sesiones,
- consultar por ID,
- listar por usuario,
- actualizar,
- eliminar.

Observaciones:

- al crear se valida el usuario,
- no se valida explícitamente que `id_compute_status` exista antes de insertar.

## 8.8 Tipos de métrica - `/metric-types`

Funcionalidades:

- crear tipo de métrica,
- validar unicidad por nombre al crear,
- listar,
- consultar por ID,
- actualizar,
- eliminar.

Caso de uso:

- parametrizar métricas medibles o derivadas.

## 8.9 Mediciones - `/Measurements`

Funcionalidades:

- crear medición validando sesión y tipo de métrica,
- listar mediciones,
- consultar por ID,
- listar por sesión,
- actualizar,
- eliminar.

Observaciones:

- el prefijo usa `/Measurements` con `M` mayúscula, a diferencia del resto de rutas.

## 8.10 Niveles de severidad - `/severity-levels`

Funcionalidades:

- crear severidad,
- evitar duplicados por nombre,
- listar,
- consultar por ID,
- actualizar,
- eliminar.

Caso de uso:

- catálogo de criticidad para alertas.

## 8.11 Alertas - `/alerts`

Funcionalidades:

- crear alerta validando sesión y severidad,
- listar alertas,
- consultar por ID,
- listar alertas por sesión,
- actualizar,
- eliminar.

Caso de uso:

- registrar eventos relevantes asociados a una sesión.

## 8.12 Estados de cómputo - `/compute_statuses`

Funcionalidades:

- crear estado,
- listar estados,
- actualizar,
- eliminar.

Observaciones:

- no existe endpoint `GET /compute_statuses/{id}`.

## 8.13 Muestras PPG - `/ppg_samples`

Funcionalidades:

- crear muestra individual,
- listar muestras,
- listar muestras por sesión,
- actualizar,
- eliminar,
- inserción masiva con `POST /ppg_samples/bulk`.

Caso de uso:

- almacenamiento de señal cruda.

Observación importante:

- la inserción masiva usa `bulk_save_objects` y no valida previamente que cada `id_session` exista.

---

## 9. Sistema de consulta dinámica

Uno de los componentes más reutilizables del proyecto es `utils/query_builder.py`.

### Capacidades soportadas

#### 1. Filtro simple

```http
?query=name:Colombia
```

#### 2. Múltiples filtros

```http
?query=id_user:1,id_metric_type:2
```

Se combinan con `AND`.

#### 3. Operadores

Soporta:

- `eq`
- `gt`
- `lt`
- `gte`
- `lte`
- `contains`
- `in`

Ejemplos:

```http
?query=value__gte:60
?query=name__contains:heart
?query=id_user__in:1|2|3
```

#### 4. Filtros por relaciones anidadas

Permite navegar relaciones usando notación por puntos.

Ejemplos:

```http
?query=id_session.id_user:1
?query=id_session.id_user.id_city:2
?query=id_session.id_user.id_city.id_country:3
```

Esto hace `JOIN` internos de forma dinámica.

#### 5. Ordenamiento

```http
?orderBy=created_at&sort=desc
```

#### 6. Paginación

```http
?limit=20&offset=40
```

### Valor técnico de este módulo

Este archivo evita repetir lógica de consulta en cada endpoint y vuelve a la API más flexible para consumo desde frontend, dashboards o scripts analíticos.

---

## 10. Relación entre módulos

La composición del sistema puede entenderse así:

### Capa geográfica

- `Country`
- `City`

Sirve para ubicar usuarios.

### Capa de identidad y perfil

- `App_user`
- `HealthRecord`

Gestiona quién es el usuario y cuál es su estado físico básico.

### Capa de dispositivos

- `WearableModel`
- `Wearable`

Modela el hardware que genera datos.

### Capa de monitoreo

- `MonitoringSession`
- `PpgSample`
- `Measurement`
- `MetricType`
- `ComputeStatus`

Modela el proceso de captura, análisis y resultado.

### Capa de eventos y riesgo

- `Alert`
- `SeverityLevel`

Permite registrar condiciones importantes detectadas en una sesión.

---

## 11. Flujo funcional del negocio

Un flujo razonable de uso del sistema sería:

1. Crear países y ciudades.
2. Crear usuarios asignados a una ciudad.
3. Registrar historial de salud del usuario.
4. Registrar modelos de wearable.
5. Asociar wearables concretos a usuarios.
6. Definir estados de cómputo.
7. Crear una sesión de monitoreo para un usuario.
8. Registrar muestras PPG crudas durante la sesión.
9. Registrar mediciones calculadas o capturadas.
10. Generar alertas con su severidad correspondiente.

Este flujo deja claro que `MonitoringSession` es la entidad operativa central del sistema.

---

## 12. Estado técnico actual

### Fortalezas

- estructura clara por módulos,
- separación razonable entre rutas, modelos y schemas,
- uso correcto de dependencias de FastAPI,
- soporte flexible de filtros, orden y paginación,
- relaciones ORM suficientemente expresivas para el dominio.

### Limitaciones u observaciones

- no hay autenticación ni autorización,
- no hay hashing de contraseñas,
- no hay migraciones de base de datos,
- no hay tests automatizados,
- no hay capa de servicios separada de las rutas,
- hay inconsistencias de naming entre carpetas y contenido:
  - `DTO/models.py` contiene ORM,
  - `ORM/schemas.py` contiene Pydantic,
- hay inconsistencias de naming en rutas:
  - `/App_users`
  - `/Measurements`
  - kebab-case en otras rutas,
- no todos los `PUT` revalidan integridad referencial con el mismo rigor,
- no todos los recursos tienen endpoint `GET por ID`,
- el README es más corto que la complejidad real del proyecto.

### Detalles puntuales del código

- en `City` aparece `id_country` declarado dos veces dentro del modelo,
- en `MonitoringSession` la relación `user` también aparece repetida,
- la API usa `data.dict()`; si se migra a Pydantic v2 estricto, conviene revisar si el proyecto quiere estandarizar `model_dump()`,
- `bulk_save_objects` en muestras PPG prioriza velocidad, pero sacrifica validaciones por registro.

---

## 13. Tecnologías utilizadas

- **Python**
- **FastAPI**
- **SQLAlchemy**
- **Pydantic**
- **Uvicorn**
- **PostgreSQL**
- **python-dotenv**

---

## 14. Ejecución del proyecto

### Instalar dependencias

```bash
pip install -r requeriment.txt
```

### Configurar variables de entorno

Crear o ajustar `.env` con:

```env
DATABASE_URL=postgresql://usuario:password@host:5432/PPG_DB
```

### Ejecutar servidor

```bash
uvicorn main:app --reload
```

### Documentación automática

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 15. Resumen ejecutivo

Este proyecto implementa una API backend para un sistema de monitoreo PPG con enfoque CRUD y persistencia relacional. Su centro funcional es la gestión de usuarios, wearables y sesiones de monitoreo, donde cada sesión puede almacenar señal cruda (`PpgSample`), métricas procesadas (`Measurement`) y alertas (`Alert`).

No es todavía una plataforma completa de producción, porque le faltan piezas importantes como autenticación, seguridad de contraseñas, migraciones y pruebas. Aun así, la base estructural está bien definida y el modelo de datos representa correctamente un dominio de monitoreo biomédico o fisiológico.

---

## 16. Archivo clave para entender rápido el proyecto

Si alguien nuevo entra al repositorio, el orden recomendado para leer el sistema es:

1. `main.py`
2. `DTO/models.py`
3. `ORM/schemas.py`
4. `utils/query_builder.py`
5. `routes/monitoring_session.py`
6. `routes/ppg_sample.py`
7. `routes/measurement.py`
8. el resto de rutas CRUD

Ese recorrido permite entender primero la composición general, luego el dominio de datos y finalmente el comportamiento HTTP.
