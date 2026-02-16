---
title: "Monitorizar servidores Linux con Prometheus y Grafana"
description: "Guía paso a paso para desplegar un stack de monitorización con Prometheus y Grafana en servidores Linux usando Node Exporter."
author: "eloculto"
pubDate: 2025-02-14
updatedDate: 2025-02-14
category: "Monitorización"
tags: ["Monitorización", "Prometheus", "Grafana", "Sysadmin"]
image: "/images/linux-monitoring.jpg"
draft: false
---

## Por qué monitorizar

Sin monitorización, los problemas se detectan cuando ya es demasiado tarde. Un stack basado en Prometheus y Grafana permite recopilar métricas, configurar alertas y visualizar el estado de toda tu infraestructura desde un solo panel.

## Arquitectura del stack

El flujo es sencillo:

1. **Node Exporter** expone métricas del sistema (CPU, RAM, disco, red) en cada servidor
2. **Prometheus** recopila esas métricas periódicamente (scraping)
3. **Grafana** las visualiza en dashboards interactivos

## Instalar Node Exporter en los servidores

Node Exporter se ejecuta en cada máquina que quieras monitorizar.

```bash
# Descargar la última versión
wget https://github.com/prometheus/node_exporter/releases/download/v1.8.1/node_exporter-1.8.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.8.1.linux-amd64.tar.gz
sudo mv node_exporter-1.8.1.linux-amd64/node_exporter /usr/local/bin/
```

Crear el servicio de systemd:

```bash
sudo cat <<EOF > /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF
```

Activar y arrancar:

```bash
sudo useradd -rs /bin/false node_exporter
sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
```

Las métricas estarán disponibles en `http://servidor:9100/metrics`.

## Instalar Prometheus

En el servidor central de monitorización:

```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.53.0/prometheus-2.53.0.linux-amd64.tar.gz
tar xvfz prometheus-2.53.0.linux-amd64.tar.gz
sudo mv prometheus-2.53.0.linux-amd64/{prometheus,promtool} /usr/local/bin/
sudo mkdir -p /etc/prometheus /var/lib/prometheus
```

### Configurar los targets

Edita `/etc/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "nodos"
    static_configs:
      - targets:
          - "192.168.1.10:9100"
          - "192.168.1.11:9100"
          - "192.168.1.12:9100"
```

### Crear el servicio

```bash
sudo cat <<EOF > /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus
After=network.target

[Service]
User=prometheus
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus

[Install]
WantedBy=multi-user.target
EOF

sudo useradd -rs /bin/false prometheus
sudo chown -R prometheus: /var/lib/prometheus /etc/prometheus
sudo systemctl daemon-reload
sudo systemctl enable --now prometheus
```

Prometheus estará accesible en `http://servidor:9090`.

## Instalar Grafana

```bash
sudo dnf install -y https://dl.grafana.com/oss/release/grafana-11.1.0-1.x86_64.rpm
sudo systemctl enable --now grafana-server
```

Accede a `http://servidor:3000` (usuario y contraseña por defecto: `admin`/`admin`).

### Conectar con Prometheus

1. Ve a **Connections > Data Sources > Add data source**
2. Selecciona **Prometheus**
3. En URL introduce `http://localhost:9090`
4. Pulsa **Save & Test**

### Importar un dashboard

El dashboard más popular para Node Exporter es el **1860**:

1. Ve a **Dashboards > Import**
2. Introduce el ID `1860`
3. Selecciona la fuente de datos Prometheus
4. Pulsa **Import**

Tendrás un panel completo con CPU, memoria, disco, red y más para cada servidor.

## Consultas PromQL útiles

Algunas queries que puedes usar en Grafana o directamente en Prometheus:

```promql
# Uso de CPU por nodo (porcentaje)
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memoria usada (porcentaje)
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Espacio en disco usado (porcentaje)
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100

# Tráfico de red recibido (bytes/s)
rate(node_network_receive_bytes_total{device="eth0"}[5m])
```

## Configurar alertas básicas

Crea un archivo de reglas `/etc/prometheus/alerts.yml`:

```yaml
groups:
  - name: nodos
    rules:
      - alert: NodoCaido
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Nodo {{ $labels.instance }} no responde"

      - alert: DiscoLleno
        expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disco al {{ $value | humanizePercentage }} en {{ $labels.instance }}"
```

Añade la referencia en `prometheus.yml`:

```yaml
rule_files:
  - "alerts.yml"
```

Reinicia Prometheus para aplicar:

```bash
sudo systemctl restart prometheus
```

## Conclusión

Con Prometheus, Node Exporter y Grafana tienes un stack de monitorización completo y gratuito. El siguiente paso natural es añadir Alertmanager para enviar notificaciones por email, Slack o Telegram cuando salten las alertas.
