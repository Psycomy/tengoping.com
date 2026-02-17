---
title: "Alertas inteligentes con Alertmanager y Prometheus"
description: "Configura alertas efectivas con Alertmanager: routing, agrupación, silenciamiento y buenas prácticas para evitar la fatiga de alertas en tu infraestructura."
author: "antonio"
pubDate: 2026-02-16
category: "Monitorización"
tags: ["alertmanager", "prometheus", "alertas", "monitoring"]
image: "../../assets/images/mon-alertmanager.jpg"
draft: false
---

## El síndrome del pastor mentiroso

Son las tres de la madrugada y tu teléfono no para de sonar. Cinco alertas de CPU al 80%, tres de disco casi lleno en servidores de staging, dos de latencia elevada que se resolvieron solas hace veinte minutos. Ninguna requiere acción inmediata. Silencias el móvil y vuelves a dormir. A las seis, descubres que entre todo ese ruido se coló una alerta real: la base de datos de producción se quedó sin conexiones disponibles y el servicio estuvo caído dos horas.

Este escenario tiene nombre: **fatiga de alertas**. Cuando todo alerta, nada alerta. Tu sistema de monitorización se convierte en el pastor que gritaba "¡lobo!" y el equipo aprende a ignorarlo. El problema no es Prometheus, que hace un trabajo excelente recopilando métricas. El problema es qué haces con esas métricas una vez que cruzan un umbral.

Ahí entra **Alertmanager**: el componente de Prometheus diseñado específicamente para gestionar el ciclo de vida de las alertas. No se limita a reenviar notificaciones; agrupa, deduplica, silencia, inhibe y enruta alertas hacia los canales correctos. En este artículo vas a configurarlo desde cero para transformar un sistema ruidoso en uno que solo te despierte cuando realmente importa.

## Requisitos previos

Antes de empezar, necesitas tener lo siguiente en marcha:

- **Prometheus funcionando** con al menos un target configurado (node_exporter, por ejemplo).
- **Acceso al servidor** donde corre Prometheus para editar archivos de configuración.
- **Alertmanager instalado**. Si usas paquetes del sistema o Docker, el binario se llama `alertmanager`. Para instalarlo manualmente:

```bash
# Descargar la última versión estable
wget https://github.com/prometheus/alertmanager/releases/download/v0.27.0/alertmanager-0.27.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.27.0.linux-amd64.tar.gz
cd alertmanager-0.27.0.linux-amd64
./alertmanager --config.file=alertmanager.yml
```

Alertmanager escucha por defecto en el puerto `9093`. Verifica que está arriba accediendo a `http://tu-servidor:9093`.

## Arquitectura general

El flujo de alertas sigue este camino:

1. **Prometheus evalúa reglas** definidas en ficheros de reglas (`rules.yml`). Cuando una condición se cumple durante el tiempo especificado, la alerta pasa a estado `firing`.
2. **Prometheus envía la alerta** a Alertmanager a través de su API.
3. **Alertmanager procesa la alerta**: la agrupa con otras similares, decide si debe inhibirse o silenciarse, y la enruta al receptor adecuado.
4. **El receptor entrega la notificación**: email, Slack, PagerDuty, webhook, Telegram u otros.

La separación es deliberada. Prometheus se encarga de decidir *qué* está mal. Alertmanager se encarga de decidir *a quién* avisar, *cuándo* y *cómo*.

## Conectar Prometheus con Alertmanager

Lo primero es decirle a Prometheus dónde encontrar Alertmanager y qué ficheros de reglas debe cargar. Edita tu `prometheus.yml`:

```yaml
# prometheus.yml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "localhost:9093"

rule_files:
  - "rules/*.yml"
```

Crea el directorio `rules/` junto a tu `prometheus.yml` si no existe:

```bash
mkdir -p /etc/prometheus/rules
```

## Definir reglas de alerta

Las reglas de alerta son la pieza que transforma métricas en eventos accionables. Cada regla tiene una expresión PromQL, una duración mínima (`for`) y etiquetas que Alertmanager usará para enrutar.

Crea el fichero `/etc/prometheus/rules/alertas-nodo.yml`:

```yaml
groups:
  - name: alertas_nodo
    rules:
      # Instancia caída durante más de 2 minutos
      - alert: InstanciaCaida
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Instancia {{ $labels.instance }} caída"
          description: "La instancia {{ $labels.instance }} del job {{ $labels.job }} lleva más de 2 minutos sin responder."

      # Uso de CPU sostenido por encima del 90%
      - alert: CpuElevado
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU por encima del 90% en {{ $labels.instance }}"
          description: "El uso medio de CPU en {{ $labels.instance }} lleva más de 10 minutos por encima del 90%. Valor actual: {{ $value | printf \"%.1f\" }}%."

      # Disco con menos del 10% de espacio libre
      - alert: DiscoLleno
        expr: (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disco casi lleno en {{ $labels.instance }}"
          description: "El sistema de ficheros {{ $labels.mountpoint }} en {{ $labels.instance }} tiene menos del 10% libre."

      # Más del 85% de memoria en uso
      - alert: MemoriaAlta
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Memoria alta en {{ $labels.instance }}"
          description: "El uso de memoria en {{ $labels.instance }} supera el 85% desde hace 10 minutos. Valor actual: {{ $value | printf \"%.1f\" }}%."
```

Fíjate en algunos detalles importantes:

- **El campo `for`** es tu primera línea de defensa contra el ruido. Un pico de CPU de 30 segundos no debería despertar a nadie. Diez minutos sostenidos sí merecen atención.
- **Las etiquetas `severity`** son arbitrarias, pero por convención se usan `critical`, `warning` e `info`. Alertmanager las usará para enrutar.
- **Las anotaciones** (`annotations`) no afectan al enrutamiento, pero aparecen en las notificaciones. Usa plantillas Go para incluir valores dinámicos.

Valida la configuración antes de recargar:

```bash
promtool check rules /etc/prometheus/rules/alertas-nodo.yml
# Recargar Prometheus sin reiniciar
curl -X POST http://localhost:9090/-/reload
```

## Configurar Alertmanager

Aquí es donde la magia ocurre. El fichero `alertmanager.yml` controla el enrutamiento, los receptores y los comportamientos de agrupación. Este es un ejemplo completo y funcional:

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_from: "alertas@tudominio.com"
  smtp_smarthost: "smtp.tudominio.com:587"
  smtp_auth_username: "alertas@tudominio.com"
  smtp_auth_password: "tu-password-smtp"
  smtp_require_tls: true
  slack_api_url: "https://hooks.slack.com/services/TU_WORKSPACE/TU_CANAL/TU_TOKEN"

# Plantillas personalizadas (opcional)
templates:
  - "/etc/alertmanager/templates/*.tmpl"

# Árbol de enrutamiento
route:
  # Receptor por defecto
  receiver: "slack-general"

  # Tiempo de espera para agrupar alertas nuevas del mismo grupo
  group_wait: 30s

  # Intervalo entre notificaciones del mismo grupo si hay alertas nuevas
  group_interval: 5m

  # Intervalo entre reenvío de alertas ya notificadas que siguen activas
  repeat_interval: 4h

  # Agrupar alertas por estas etiquetas
  group_by: ["alertname", "severity"]

  # Rutas hijas (se evalúan en orden)
  routes:
    # Alertas críticas van por email y Slack
    - match:
        severity: critical
      receiver: "equipo-criticas"
      repeat_interval: 1h
      continue: false

    # Alertas warning solo a Slack
    - match:
        severity: warning
      receiver: "slack-general"
      repeat_interval: 6h

# Receptores
receivers:
  - name: "slack-general"
    slack_configs:
      - channel: "#monitoring"
        title: '{{ .GroupLabels.alertname }} [{{ .Status | toUpper }}]'
        text: >-
          {{ range .Alerts }}
          *{{ .Annotations.summary }}*
          {{ .Annotations.description }}
          {{ end }}
        send_resolved: true

  - name: "equipo-criticas"
    email_configs:
      - to: "oncall@tudominio.com"
        send_resolved: true
    slack_configs:
      - channel: "#criticas"
        title: 'CRITICO: {{ .GroupLabels.alertname }}'
        text: >-
          {{ range .Alerts }}
          *{{ .Annotations.summary }}*
          {{ .Annotations.description }}
          {{ end }}
        send_resolved: true

# Reglas de inhibición
inhibit_rules:
  # Si una instancia está caída, no enviar alertas de CPU/memoria/disco
  - source_match:
      alertname: "InstanciaCaida"
    target_match_re:
      alertname: "CpuElevado|MemoriaAlta|DiscoLleno"
    equal: ["instance"]
```

Valida el fichero antes de arrancar:

```bash
amtool check-config /etc/alertmanager/alertmanager.yml
```

### El árbol de enrutamiento

El bloque `route` funciona como un árbol. Cada alerta entra por la raíz y desciende por las ramas (`routes`) hasta encontrar una coincidencia. Si ninguna ruta hija coincide, se usa el receptor de la raíz.

El campo `continue: false` (que es el valor por defecto) detiene la evaluación en la primera coincidencia. Si lo cambias a `continue: true`, la alerta seguirá evaluando las rutas siguientes, lo que te permite enviar la misma alerta a varios receptores.

### Agrupación con group_by

La agrupación es la funcionalidad más útil de Alertmanager para reducir ruido. Si cinco servidores disparan `DiscoLleno` al mismo tiempo, en lugar de recibir cinco mensajes, recibes uno solo que los agrupa todos.

`group_by: ["alertname", "severity"]` significa que todas las alertas con el mismo nombre y severidad se meten en un solo grupo. Puedes ajustarlo según tus necesidades. Por ejemplo, `group_by: ["cluster", "alertname"]` agrupa por clúster, útil si gestionas varios entornos.

Los tiempos de agrupación también importan:

- **`group_wait`**: cuánto espera Alertmanager antes de enviar la primera notificación de un grupo nuevo. Esto permite que si tres servidores caen con 15 segundos de diferencia, lleguen en un solo mensaje.
- **`group_interval`**: si ya se envió una notificación y llegan alertas nuevas al mismo grupo, cuánto esperar antes de enviar una actualización.
- **`repeat_interval`**: si nada cambia en el grupo, cuánto esperar antes de recordar que la alerta sigue activa.

### Inhibición

Las reglas de inhibición suprimen alertas que no tienen sentido cuando otra alerta ya está activa. En nuestro ejemplo, si `InstanciaCaida` está disparada para el servidor `web-01`, no tiene sentido recibir además `CpuElevado`, `MemoriaAlta` o `DiscoLleno` para ese mismo servidor. Obviamente todo va a estar mal si la máquina está caída.

El campo `equal: ["instance"]` asegura que la inhibición solo se aplique cuando ambas alertas comparten la misma instancia.

### Silenciamiento

Los silencios son temporales y se crean desde la interfaz web de Alertmanager o con `amtool`. Son ideales para ventanas de mantenimiento:

```bash
# Silenciar todas las alertas de un servidor durante 2 horas
amtool silence add instance="web-03:9100" \
  --duration=2h \
  --author="antonio" \
  --comment="Mantenimiento programado: actualización de kernel"

# Listar silencios activos
amtool silence query

# Eliminar un silencio por ID
amtool silence expire <silence-id>
```

## Añadir un receptor webhook

Para integraciones personalizadas (Telegram, Discord, sistemas de ticketing), puedes usar un receptor webhook que envía un POST con el JSON de las alertas:

```yaml
receivers:
  - name: "webhook-custom"
    webhook_configs:
      - url: "http://localhost:8090/alertmanager"
        send_resolved: true
        max_alerts: 0
```

El JSON que recibe tu endpoint incluye todas las alertas del grupo con sus etiquetas y anotaciones. Puedes escribir un pequeño servicio que lo parsee y lo envíe a donde necesites.

## Buenas prácticas contra la fatiga de alertas

Tener Alertmanager configurado es solo la mitad del trabajo. Estas prácticas marcan la diferencia entre un sistema de alertas útil y uno que tu equipo ignora:

### Alerta sobre síntomas, no sobre causas

No alertes porque el CPU está al 85%. Alerta porque el tiempo de respuesta de tu API ha superado el SLO. El CPU alto puede ser normal durante un despliegue; la degradación del servicio nunca lo es.

### Cada alerta debe tener una acción clara

Si quien recibe la alerta no puede hacer nada al respecto, esa alerta no debería existir. Antes de crear una regla, pregúntate: "¿Qué haría yo al recibir esto a las tres de la madrugada?" Si la respuesta es "esperar a que se resuelva solo", no es una alerta, es una métrica para un dashboard.

### Usa severidades con criterio

Una clasificación razonable sería:

- **critical**: requiere acción inmediata, despierta a alguien.
- **warning**: requiere atención en horario laboral.
- **info**: solo informativa, se revisa en el dashboard.

Solo `critical` debería generar notificaciones fuera de horario. Las alertas `warning` pueden acumularse y revisarse por la mañana.

### Ajusta los umbrales con datos reales

Empieza con umbrales conservadores y ajústalos según el comportamiento real de tu infraestructura. Si una alerta se dispara constantemente sin que nadie actúe, sube el umbral o elimínala. Si un incidente real no generó alerta, baja el umbral o crea una regla nueva.

### Revisa las alertas periódicamente

Agenda una revisión mensual de tus reglas de alerta. Elimina las que nadie atiende, ajusta las que generan ruido y añade las que faltan según los incidentes recientes.

## Verificar que todo funciona

Una vez configurado todo, comprueba que las alertas llegan correctamente:

```bash
# Disparar una alerta de prueba manualmente
amtool alert add test_alerta severity=critical \
  instance="test-server:9100" \
  --annotation.summary="Alerta de prueba" \
  --annotation.description="Verificando la cadena de notificaciones"

# Ver alertas activas
amtool alert query

# Eliminar la alerta de prueba
amtool alert add test_alerta severity=critical \
  instance="test-server:9100" --end=now
```

Revisa también la interfaz web de Alertmanager en `http://tu-servidor:9093` para ver el estado de las alertas, los silencios activos y los grupos.

## Siguiente paso

Con Alertmanager funcionando, el siguiente paso natural es implementar **Grafana OnCall** o **PagerDuty** para gestionar guardias y escalados. Alertmanager se encarga del enrutamiento inicial, pero un sistema de gestión de incidencias te permite definir rotaciones de guardia, escalados automáticos si nadie responde y un registro completo de cada incidente. También vale la pena explorar las **alerting rules basadas en recording rules** para simplificar expresiones PromQL complejas y mejorar el rendimiento de la evaluación.
