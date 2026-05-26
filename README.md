# Módulo de Revisión y Auditoría de Red ODN

Sistema de auditoría de planta externa para ISPs. Permite gestionar tramos OTDR, módulos SFP, mediciones de potencia en campo, alertas de seguridad industrial y generación de actas de entrega técnica con firma digital.

**Stack:** FastAPI · SvelteKit · PostgreSQL 16 · Docker

---

## Requisitos previos

| Herramienta | Versión mínima | Descarga |
|---|---|---|
| Docker Desktop | 4.x | https://www.docker.com/products/docker-desktop |
| Git | cualquiera | https://git-scm.com |

> Docker Desktop incluye `docker compose` (v2). No se necesita nada más para correr el sistema completo.

---

## 1. Clonar el repositorio

```bash
git clone https://github.com/Jvasquez77/auditoriadered.git
cd auditoriadered
```

---

## 2. Instalar Docker Desktop

### macOS
1. Descarga Docker Desktop desde https://www.docker.com/products/docker-desktop
2. Abre el archivo `.dmg` descargado y arrastra Docker a la carpeta Aplicaciones
3. Abre Docker desde Aplicaciones — aparecerá el ícono de la ballena en la barra de menú
4. Espera a que el ícono deje de animarse (Docker está listo cuando dice "Running")

Verifica la instalación:
```bash
docker --version
docker compose version
```

### Windows
1. Descarga Docker Desktop desde https://www.docker.com/products/docker-desktop
2. Ejecuta el instalador `.exe` y sigue los pasos (requiere reiniciar)
3. Abre Docker Desktop desde el menú Inicio
4. Acepta los términos de uso en la primera ejecución

Verifica en PowerShell o CMD:
```bash
docker --version
docker compose version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

---

## 3. Configurar variables de entorno

Copia el archivo de ejemplo de configuración del backend:

```bash
cp backend/.env.example backend/.env
```

El archivo `.env` generado funciona sin cambios para desarrollo local. Los valores por defecto son:

| Variable | Valor | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/network_audit_db` | Conexión a PostgreSQL |
| `OTDR_MAX_FUSION_LOSS_DB` | `0.1` | Pérdida máxima por fusión (dB) |
| `SFP_MIN_TX_POWER_DBM` | `6.0` | Potencia mínima de TX del SFP (dBm) |
| `CLIENT_CRITICAL_POWER_DBM` | `-25.4` | Umbral de potencia crítica del cliente |
| `DEBUG` | `true` | Modo debug activado |

> Para producción edita estos valores según los umbrales operacionales de tu red.

---

## 4. Levantar el sistema con Docker

```bash
docker compose up -d --build
```

Este comando:
1. Descarga las imágenes base (Node 22, Python 3.12, PostgreSQL 16) — solo la primera vez
2. Instala las dependencias de Python y Node dentro de los contenedores
3. Crea la base de datos y aplica el esquema SQL automáticamente
4. Levanta los 3 servicios en segundo plano

Espera unos 30-60 segundos la primera vez. Verifica que todo esté corriendo:

```bash
docker compose ps
```

Deberías ver los 3 servicios en estado `Up` o `healthy`:

```
NAME                    STATUS
network_audit_db        Up (healthy)
network_audit_api       Up
network_audit_frontend  Up
```

---

## 5. Acceder a la aplicación

| Servicio | URL | Descripción |
|---|---|---|
| **Frontend** | http://localhost:5173/network-audit | Interfaz principal |
| **API REST** | http://localhost:8000 | Backend FastAPI |
| **Documentación API** | http://localhost:8000/docs | Swagger UI interactivo |
| **PostgreSQL** | `localhost:5432` | Base de datos (usuario: `postgres`, contraseña: `postgres`) |

---

## 6. Módulos disponibles

Una vez dentro del frontend (`http://localhost:5173/network-audit`) encontrarás en el menú lateral:

- **Dashboard** — Panel de control con KPIs: puertos auditados, tramos OTDR bloqueados, SFPs por cambiar, visitas técnicas pendientes, alertas de transformadores, actas aprobadas
- **Ingesta** — Carga de datos desde OLT, evaluación SFP, reflectometría OTDR, sincronización OZmap
- **Campo** — Interfaz de mediciones en calle para cuadrillas técnicas (potencia óptica por abonado)
- **Actas** — Generación y firma digital de actas de entrega técnica ODN

---

## 7. Comandos útiles

```bash
# Ver logs en tiempo real de todos los servicios
docker compose logs -f

# Ver logs solo del backend
docker compose logs -f backend

# Ver logs solo del frontend
docker compose logs -f frontend

# Detener todos los servicios
docker compose down

# Detener y eliminar la base de datos (borra todos los datos)
docker compose down -v

# Reiniciar un servicio específico
docker compose restart backend

# Reconstruir después de cambios en el código
docker compose up -d --build
```

---

## 8. Solución de problemas frecuentes

### "This site can't be reached" en localhost:5173
El contenedor del frontend aún está iniciando. Espera 15-30 segundos y recarga. Si persiste:
```bash
docker compose logs frontend
```

### Error de conexión al backend desde el frontend
Verifica que el contenedor del backend esté `Up`:
```bash
docker compose ps
docker compose logs backend
```

### "docker: command not found"
Docker Desktop no está abierto. Abre la aplicación Docker Desktop y espera a que el ícono de la ballena deje de animarse.

### El puerto 5432, 8000 o 5173 ya está en uso
Otro proceso ocupa ese puerto. Detén el proceso o cambia el puerto en `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # cambia el puerto externo
```

### Cambios en el código no se reflejan
Los volúmenes de Docker sincronizan los archivos automáticamente en modo `dev --reload`. Si el problema persiste, reconstruye:
```bash
docker compose up -d --build
```

---

## Estructura del proyecto

```
auditoriadered/
├── backend/                  # FastAPI + SQLAlchemy 2.0 async
│   ├── app/
│   │   ├── models/           # Modelos ORM (OltPort, N1Infrastructure, etc.)
│   │   ├── routers/          # Endpoints REST
│   │   ├── schemas/          # Esquemas Pydantic v2
│   │   ├── services/         # Lógica de negocio
│   │   └── main.py
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   ├── .env.example
│   └── requirements.txt
├── frontend/                 # SvelteKit 2 + Svelte 5 + Tailwind CSS
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/   # Componentes reutilizables
│   │   │   └── types/        # Tipos TypeScript
│   │   └── routes/
│   │       └── network-audit/
│   │           ├── +page.svelte         # Dashboard
│   │           ├── ingest/              # Ingesta de datos
│   │           ├── field/               # Mediciones en campo
│   │           └── certification/       # Actas de entrega
│   └── package.json
└── docker-compose.yml
```
