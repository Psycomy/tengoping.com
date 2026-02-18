---
title: 'Introducción a la observabilidad: métricas, logs y trazas'
description: 'Descubre los tres pilares de la observabilidad moderna: métricas, logs y trazas. Qué son, por qué importan y qué herramientas usar para monitorizar tu infraestructura.'
author: 'antonio'
pubDate: 2026-02-16
category: 'Monitorización'
tags: ['observabilidad', 'metricas', 'logs', 'trazas', 'monitoring']
image: '../../assets/images/mon-observabilidad.jpg'
draft: false
---

## Son las 3 de la mañana y algo falla

Imagina este escenario: te despierta una alerta de Nagios diciendo que el check de HTTP contra tu aplicación ha fallado. Te conectas por SSH, compruebas que nginx está corriendo, que el proceso de la aplicación está vivo, que el disco no está lleno. Todo parece bien. Pero los usuarios siguen reportando errores intermitentes.

Lanzas un `curl` contra el endpoint y responde en 200ms. Correcto. Pero resulta que el problema solo afecta al 5% de las peticiones, las que pasan por un microservicio que llama a una API externa que ha empezado a responder con latencias de 8 segundos. Tu monitorización clásica — basada en "¿está el servicio arriba o abajo?" — no puede ver esto.

Este es el punto exacto donde la **monitorización tradicional** se queda corta y la **observabilidad** entra en juego.

## Monitorización vs. observabilidad

Antes de entrar en detalle, conviene aclarar la diferencia porque se confunden constantemente.

**Monitorización** es reactiva: defines de antemano qué comprobar (CPU > 90%, disco > 80%, servicio caído) y recibes alertas cuando se cumple una condición. Funciona bien para fallos conocidos y predecibles.

**Observabilidad** es la capacidad de entender el estado interno de un sistema a partir de sus salidas externas. No necesitas predecir el fallo de antemano; si el sistema es observable, puedes investigar cualquier comportamiento inesperado usando los datos que ya emite.

```
┌─────────────────────────────────────────────────────┐
│              MONITORIZACIÓN CLÁSICA                  │
│                                                     │
│   ¿Está arriba?  ──→  SÍ / NO                      │
│   ¿CPU > 90%?    ──→  SÍ / NO                      │
│   ¿Disco > 80%?  ──→  SÍ / NO                      │
│                                                     │
│   Resultado: sabes QUÉ falla, pero no POR QUÉ      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              OBSERVABILIDAD                         │
│                                                     │
│   Métricas  ──→  ¿Qué está pasando ahora?          │
│   Logs      ──→  ¿Qué pasó exactamente?            │
│   Trazas    ──→  ¿Por dónde pasó la petición?       │
│                                                     │
│   Resultado: puedes investigar lo DESCONOCIDO       │
└─────────────────────────────────────────────────────┘
```

La monitorización es un subconjunto de la observabilidad. No la reemplaza, la amplía.

## Los tres pilares de la observabilidad

La observabilidad moderna se apoya en tres tipos de datos complementarios: métricas, logs y trazas. Cada uno responde a preguntas diferentes.

```
              ┌──────────────┐
              │  MÉTRICAS    │ ← ¿Cuánto? ¿Qué tan rápido?
              │  (numérico)  │
              └──────┬───────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
  ┌─────┴──────┐     │     ┌─────┴──────┐
  │   LOGS     │     │     │  TRAZAS    │
  │  (eventos) │     │     │  (flujo)   │
  └────────────┘     │     └────────────┘
   ← ¿Qué pasó?     │      ← ¿Por dónde?
                     │
           Los tres juntos
          = OBSERVABILIDAD
```

### Métricas: los números que cuentan la historia

Las métricas son valores numéricos agregados en el tiempo. Son baratas de almacenar, rápidas de consultar y perfectas para detectar tendencias y anomalías.

Ejemplos típicos:

- **Contadores**: peticiones HTTP totales, errores 5xx, bytes transmitidos
- **Gauges**: uso de CPU actual, memoria libre, conexiones activas
- **Histogramas**: distribución de latencias (p50, p95, p99)

#### Cuándo son útiles

- Detectar que la latencia p99 ha subido de 200ms a 2s
- Ver que el rate de errores 500 ha pasado del 0.1% al 5%
- Alertar cuando la cola de mensajes supera los 10.000 pendientes
- Correlacionar picos de CPU con despliegues

#### Herramientas principales

**Prometheus** es el estándar de facto para métricas en infraestructura moderna. Usa un modelo pull (él va a buscar las métricas a tus servicios) y almacena series temporales localmente.

```yaml
# prometheus.yml - configuración básica
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets:
          - 'servidor1:9100'
          - 'servidor2:9100'
          - 'servidor3:9100'

  - job_name: 'nginx'
    static_configs:
      - targets:
          - 'servidor1:9113'

  - job_name: 'aplicacion'
    metrics_path: '/metrics'
    static_configs:
      - targets:
          - 'servidor1:8080'
```

Una consulta PromQL típica para ver la tasa de errores HTTP:

```bash
# Porcentaje de errores 5xx en los últimos 5 minutos
rate(http_requests_total{status=~"5.."}[5m])
  /
rate(http_requests_total[5m])
  * 100
```

**InfluxDB** es otra opción popular, especialmente cuando ya tienes datos de Telegraf o necesitas una base de series temporales con SQL-like queries (InfluxQL o Flux).

Las métricas te dicen que algo va mal, pero no te dicen qué exactamente. Para eso necesitas logs.

### Logs: el registro detallado de los eventos

Los logs son registros de eventos discretos con texto no estructurado o semi-estructurado. Son el recurso al que todo sysadmin recurre primero: `journalctl`, `tail -f`, `grep` en `/var/log/`.

El problema no es generar logs. El problema es gestionarlos cuando tienes 50 servidores generando miles de líneas por segundo.

#### Cuándo son útiles

- Investigar el error exacto que causó un fallo (`stack trace`, mensaje de error)
- Auditar acciones de usuarios (quién hizo qué y cuándo)
- Depurar lógica de negocio ("el pedido X se procesó con estado Y")
- Buscar patrones en errores intermitentes

#### Centralización: el primer paso

Leer logs servidor por servidor no escala. Necesitas centralización.

```
┌───────────┐    ┌───────────┐    ┌───────────┐
│ Servidor 1│    │ Servidor 2│    │ Servidor 3│
│  (logs)   │    │  (logs)   │    │  (logs)   │
└─────┬─────┘    └─────┬─────┘    └─────┬─────┘
      │                │                │
      └────────────────┼────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   Recolector   │
              │ (Promtail /    │
              │  Filebeat /    │
              │  Fluentd)      │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │  Almacén de    │
              │     logs       │
              │ (Loki / ELK)  │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │  Visualización │
              │  (Grafana /    │
              │   Kibana)      │
              └────────────────┘
```

#### Herramientas principales

**ELK Stack** (Elasticsearch + Logstash + Kibana) fue durante años la referencia. Es potente para búsquedas full-text y análisis complejos, pero consume muchos recursos. Elasticsearch es intensivo en RAM y disco.

**Grafana Loki** es una alternativa más ligera. A diferencia de Elasticsearch, Loki no indexa el contenido de los logs sino solo los labels (como Prometheus). Esto lo hace mucho más barato de operar.

```yaml
# promtail.yml - enviar logs del sistema a Loki
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: syslog
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          host: servidor1
          __path__: /var/log/syslog

  - job_name: nginx
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx
          host: servidor1
          __path__: /var/log/nginx/*.log
```

Un consejo práctico: estructura tus logs en JSON siempre que puedas. La diferencia entre buscar en texto plano y filtrar por campos es enorme cuando necesitas encontrar algo rápido a las 3 de la mañana.

```bash
# Log no estructurado (difícil de filtrar)
2026-02-16 03:15:22 ERROR Failed to connect to database server db1, timeout after 5000ms

# Log estructurado en JSON (fácil de filtrar y agregar)
{"timestamp":"2026-02-16T03:15:22Z","level":"ERROR","msg":"Failed to connect to database","host":"db1","timeout_ms":5000,"service":"api-gateway"}
```

Los logs te dicen qué pasó en un servicio concreto. Pero cuando una petición atraviesa múltiples servicios, necesitas trazas.

### Trazas: siguiendo el camino de una petición

Las trazas distribuidas (distributed traces) te permiten seguir una petición individual a través de todos los servicios que toca. Cada traza se compone de spans que representan una operación dentro de un servicio.

```
Petición del usuario: GET /api/pedido/1234
│
├── [api-gateway]        12ms
│   ├── [auth-service]    3ms  → Validar token JWT
│   └── [pedidos-svc]     8ms  → Consultar pedido
│       ├── [postgres]    2ms  → SELECT * FROM pedidos
│       └── [cache]       1ms  → Redis GET pedido:1234
│
Tiempo total: 14ms (con paralelismo)
```

Sin trazas, si el endpoint `/api/pedido/1234` empieza a tardar 5 segundos, tendrías que revisar los logs de cada servicio individualmente e intentar correlacionarlos por timestamp. Con trazas, ves de un vistazo que el cuello de botella está en la consulta a PostgreSQL.

#### Cuándo son útiles

- Identificar qué servicio introduce la latencia en una cadena de llamadas
- Detectar llamadas innecesarias entre servicios (N+1 queries distribuidas)
- Entender dependencias reales entre servicios (no las documentadas, las reales)
- Depurar errores que se propagan entre microservicios

#### Herramientas principales

**Jaeger** (originalmente de Uber) y **Grafana Tempo** son las opciones más comunes en entornos open source. Ambos son compatibles con OpenTelemetry, que se ha convertido en el estándar para instrumentación.

```yaml
# docker-compose.yml - Jaeger all-in-one para desarrollo
services:
  jaeger:
    image: jaegertracing/all-in-one:1.54
    ports:
      - '16686:16686' # UI web
      - '4317:4317' # OTLP gRPC (OpenTelemetry)
      - '4318:4318' # OTLP HTTP (OpenTelemetry)
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

**OpenTelemetry** merece mención especial. No es una herramienta de almacenamiento sino un framework de instrumentación que unifica la recolección de métricas, logs y trazas. La idea es instrumentar una vez y enviar los datos al backend que prefieras.

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  prometheus:
    endpoint: '0.0.0.0:8889'
  loki:
    endpoint: 'http://loki:3100/loki/api/v1/push'
  otlp/tempo:
    endpoint: 'tempo:4317'
    tls:
      insecure: true

service:
  pipelines:
    metrics:
      receivers: [otlp]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      exporters: [loki]
    traces:
      receivers: [otlp]
      exporters: [otlp/tempo]
```

## Cómo se complementan los tres pilares

La potencia real aparece cuando los tres tipos de datos se conectan entre sí. Volvamos al escenario de las 3 de la mañana:

1. **Métricas** → La alerta salta porque la latencia p99 ha superado los 3 segundos
2. **Trazas** → Filtras por peticiones lentas y ves que el span del servicio `pagos-api` tarda 7 segundos
3. **Logs** → Buscas los logs de `pagos-api` con el trace ID y encuentras: "Connection pool exhausted, waiting for available connection"

En menos de 5 minutos has localizado la causa raíz: el pool de conexiones a la base de datos del servicio de pagos se ha saturado. Sin observabilidad habrías tardado una hora saltando entre servidores.

```
   ALERTA                  INVESTIGACIÓN              CAUSA RAÍZ
     │                          │                          │
     ▼                          ▼                          ▼
┌─────────┐  "¿Qué pasa?"  ┌─────────┐  "¿Por qué?"  ┌─────────┐
│ Métrica │ ──────────────→ │  Traza  │ ─────────────→ │   Log   │
│ p99 > 3s│                 │ pagos:7s│                │ pool    │
└─────────┘                 └─────────┘                │ exhausted│
                                                       └─────────┘
```

La clave es la **correlación**. Los tres pilares funcionan mejor cuando puedes saltar de uno a otro. Por eso herramientas como Grafana permiten enlazar métricas, logs y trazas en una misma interfaz: desde un pico en un dashboard pulsas y ves las trazas de ese periodo; desde una traza pulsas un span y ves los logs de ese servicio en ese momento.

## Por dónde empezar: un enfoque pragmático

No necesitas implementar todo a la vez. Un camino razonable para un equipo que ya hace monitorización básica:

### Fase 1: métricas con Prometheus + Grafana

Instala node_exporter en tus servidores, configura Prometheus para recogerlos y monta dashboards en Grafana. Esto ya te da visibilidad sobre CPU, memoria, disco, red y servicios.

```bash
# Instalar node_exporter en cada servidor
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xzf node_exporter-1.7.0.linux-amd64.tar.gz
sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
```

```bash
# Crear servicio systemd
sudo tee /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
```

### Fase 2: centralización de logs con Loki

Añade Promtail a tus servidores para enviar logs a Loki. Grafana ya lo tienes, así que solo necesitas añadir Loki como datasource. Empieza por los logs de sistema y nginx.

### Fase 3: trazas distribuidas

Solo cuando tengas microservicios o una arquitectura con múltiples componentes que se comunican entre sí. Si tienes un monolito, las trazas aportan poco. Empieza instrumentando con OpenTelemetry y envía a Jaeger o Tempo.

## Errores comunes que conviene evitar

- **Recopilar todo sin criterio**: más datos no significa más observabilidad. Métricas con cardinalidad explosiva (un label por usuario) o logs en modo DEBUG en producción solo generan costes y ruido.
- **No correlacionar**: tener Prometheus por un lado, ELK por otro y Jaeger en un tercer sitio sin ninguna conexión entre ellos reduce enormemente su utilidad.
- **Ignorar la retención**: define cuánto tiempo necesitas conservar cada tipo de dato. Las métricas agregadas pueden guardarse meses; los logs detallados quizá solo necesitas 15 días.
- **No estandarizar los labels**: si un servicio se llama "api-gateway" en métricas, "apigateway" en logs y "api_gateway" en trazas, correlacionar será una pesadilla.

## Siguiente paso

Si este artículo te ha dado una visión general, el siguiente paso natural es ensuciarte las manos. Mi recomendación: monta un stack de Prometheus + Grafana + Loki en un entorno de pruebas (Docker Compose es perfecto para esto) y empieza a monitorizar algo real. No necesitas un cluster de Kubernetes — tu propio servidor con node_exporter y Promtail ya te dará datos reales con los que experimentar.

En futuros artículos entraremos en detalle con cada pilar: configurar Prometheus con alertas en Alertmanager, montar un stack de Loki para centralizar logs, y cómo instrumentar aplicaciones con OpenTelemetry. Si quieres ir preparándote, echa un vistazo a la documentación oficial de [Prometheus](https://prometheus.io/docs/) y [Grafana Loki](https://grafana.com/docs/loki/latest/).
