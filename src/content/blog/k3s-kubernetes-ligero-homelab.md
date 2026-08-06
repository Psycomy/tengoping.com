---
title: 'K3s: Kubernetes ligero para tu homelab'
description: 'Instala un clúster K3s en tu homelab: nodo servidor, agentes worker, ingress con Traefik y kubectl, alternativa ligera a Kubernetes completo.'
author: 'antonio'
pubDate: 2026-08-06
category: 'Virtualización'
tags: ['K3s', 'Kubernetes', 'Virtualización', 'Homelab']
image: '../../assets/images/virt-k3s.jpg'
draft: true
---

K3s es una distribución de Kubernetes empaquetada en un único binario de menos de 70 MB, pensada para entornos con recursos limitados: edge, IoT y, muy especialmente, el homelab. Su función principal sigue siendo la misma que la de cualquier Kubernetes: orquestar contenedores de aplicación — las mismas imágenes OCI que ya generas con [Docker](/blog/docker-guia-practica-contenedores-linux/) o [Podman](/blog/introduccion-contenedores-podman-linux/) — repartiéndolos entre varias máquinas, reiniciándolos si fallan y balanceando la carga entre ellas. Si ya tienes claro cómo levantar VMs con [Proxmox VE](/blog/proxmox-ve-hipervisor-casero/) o contenedores de sistema con [Incus/LXC](/blog/incus-lxc-contenedores-sistema-linux/), piensa en K3s como la capa que decide _qué_ contenedores de aplicación corren y _dónde_, mientras que Proxmox o Incus/LXC son solo el sustrato — la máquina (virtual o de sistema) — sobre el que corre cada nodo del clúster.

## Qué es K3s y por qué no es lo mismo que un hipervisor o un contenedor

K3s, desarrollado originalmente por Rancher Labs y hoy proyecto de la CNCF, es una distribución certificada de Kubernetes que recorta componentes poco usados en despliegues pequeños y sustituye piezas pesadas por alternativas más ligeras, sin dejar de ser Kubernetes real (pasa la suite de conformidad CNCF). Según la documentación oficial y el propio proyecto en GitHub, las diferencias principales frente a un Kubernetes "vanilla" son:

- **Un solo binario:** el servidor empaqueta el API server, el scheduler, el controller manager, kubelet y kube-proxy en un mismo proceso, en lugar de repartirlos en servicios independientes.
- **containerd embebido** como runtime de contenedores, así que no necesitas instalarlo ni configurarlo aparte.
- **SQLite como datastore por defecto** en lugar de etcd, adecuado para un único nodo servidor; para alta disponibilidad, K3s puede usar un etcd embebido o una base de datos externa (MySQL, MariaDB, PostgreSQL).
- **Flannel** como plugin de red (CNI) por defecto, en vez de dejarte elegir entre varias opciones.
- **Traefik** como controlador de ingress por defecto, junto con un balanceador de servicio ligero propio (ServiceLB, antes llamado Klipper) que expone servicios `LoadBalancer` sin depender de un balanceador externo como MetalLB.

Aquí es donde conviene ser preciso sobre qué orquesta realmente Kubernetes, porque es fácil confundir capas. Un **pod** —la unidad mínima que programa K3s— es, en la práctica, uno o más contenedores de aplicación: el mismo tipo de contenedor OCI que arrancarías con `docker run` o `podman run`, ejecutado por `containerd` (el runtime que K3s trae embebido). De hecho, una imagen construida con `docker build` funciona sin cambios en un pod de K3s, porque ambos cumplen la especificación OCI de imágenes — es la razón por la que Kubernetes dejó de depender de Docker como runtime desde la versión 1.24 sin que ningún `Dockerfile` existente dejara de funcionar. Si ya conoces [Docker](/blog/docker-guia-practica-contenedores-linux/) o [Podman](/blog/introduccion-contenedores-podman-linux/), la función de K3s no es sustituir esa capa, sino decidir en cuál de varias máquinas ejecutar cada uno de esos contenedores, reiniciarlos si fallan y exponerlos en red — algo que Docker/Podman por sí solos no hacen cuando tienes más de un host.

Esas "varias máquinas" (nodos, en la jerga de Kubernetes) son la otra capa, y es donde entran Proxmox e Incus/LXC — pero solo como el sustrato, no como lo que se orquesta. Proxmox VE es un hipervisor tipo 1, virtualiza hardware completo para correr sistemas operativos enteros; Incus/LXC gestiona contenedores de sistema, procesos aislados que comparten el kernel del host. Un nodo K3s puede ser una VM de Proxmox con Linux instalado, un servidor físico, o —con matices, ver más abajo— un contenedor LXC. K3s no impone nada sobre esa capa: solo necesita un Linux con acceso de red al servidor. Es una capa de orquestación de contenedores de aplicación que se apoya encima de las capas de virtualización o contenedor de sistema, no un sustituto de ellas.

## Arquitectura de un clúster K3s

Un clúster mínimo tiene un nodo servidor (control plane) y uno o más nodos agente (workers). El servidor expone la API de Kubernetes en el puerto 6443 y coordina la programación de pods; los agentes se registran contra él usando un token compartido y ejecutan la carga de trabajo real.

```
Nodo servidor  k3s-server-01  (control plane + datastore SQLite)
   │
   │ API Kubernetes, puerto 6443/TCP
   │ token de unión: /var/lib/rancher/k3s/server/node-token
   │
   ├── Nodo agente  k3s-agent-01  → pods de la app (ej. nginx-demo)
   ├── Nodo agente  k3s-agent-02  → pods de la app (ej. nginx-demo)
   │
   ▼
Traefik (ingress controller, incluido por defecto)
   │
   └── expone los Services hacia el resto de la red del homelab
```

Cada nodo agente puede ser, por ejemplo, una VM ligera creada en Proxmox — la opción más simple y la que se usa en el resto de este artículo.

> [!WARNING]
> También es posible correr K3s dentro de un contenedor LXC/Incus, pero no es un caso equivalente a una VM: K3s necesita gestionar sus propias interfaces de red y cgroups, así que el contenedor debe ser **privilegiado** (sin la opción "unprivileged"), con _nesting_ habilitado y AppArmor desactivado. En un contenedor privilegiado, un escape de root desde dentro da acceso de root al host — un riesgo real que no existe con una VM. Si no tienes una razón concreta para ahorrar los recursos de una VM completa, usa VMs para los nodos de K3s.

## Requisitos previos

Según los requisitos oficiales de K3s (`docs.k3s.io/installation/requirements`), para un homelab modesto necesitas:

- **Nodo servidor:** mínimo 2 CPU y 2 GB de RAM.
- **Nodo agente:** mínimo 1 CPU y 512 MB de RAM (en la práctica, para correr aplicaciones reales conviene bastante más).
- **Hostname único por nodo** — si no lo es, tendrás que fijar `K3S_NODE_NAME` con un valor distinto en cada máquina.
- **Puertos accesibles entre nodos:** 6443/TCP (API de Kubernetes), 8472/UDP (VXLAN de Flannel), 10250/TCP (métricas del kubelet) y, si usas el backend WireGuard de Flannel, 51820-51821/UDP.
- Arquitecturas soportadas: x86_64, arm64/aarch64 y armhf (Raspberry Pi incluida, aunque se recomienda SSD externo en vez de tarjeta SD por el rendimiento del datastore).

> [!TIP]
> Si tus nodos están en la misma VLAN del homelab y ya usas un firewall a nivel de switch o router, puedes simplificar mucho: los tres puertos anteriores son los únicos imprescindibles entre servidor y agentes.

## Despliegue paso a paso

### 1. Instalar el nodo servidor

En la máquina que hará de control plane (una VM de Proxmox o un servidor físico), ejecuta el script de instalación oficial:

```bash
curl -sfL https://get.k3s.io | sh -
```

El instalador configura K3s como servicio systemd (o OpenRC), lo deja arrancando automáticamente en cada reinicio y añade utilidades adicionales: `kubectl`, `crictl`, `ctr` y los scripts `k3s-killall.sh` y `k3s-uninstall.sh`.

Comprueba que el servicio está activo:

```bash
sudo systemctl status k3s
sudo k3s kubectl get nodes
```

El comando `k3s kubectl` es un wrapper que usa el `kubectl` embebido apuntando al kubeconfig del propio servidor (`/etc/rancher/k3s/k3s.yaml`), útil para verificar el estado sin configurar nada más.

### 2. Recuperar el token de unión

El servidor genera un token que los agentes necesitan para autenticarse contra el clúster. Se guarda en:

```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

> [!IMPORTANT]
> Este token concede permiso para unir nodos completos al clúster — quien lo tenga puede añadir un agente y ejecutar cargas de trabajo con acceso a la red del clúster. Trátalo como una credencial: no lo pegues en tickets, chats ni repos públicos. Restringe el acceso al archivo con permisos de solo root (`chmod 600`), y si sospechas que se ha filtrado, K3s permite rotarlo regenerando el servidor con un nuevo valor de `--token` o usando `--token-file` con un secreto gestionado aparte.

### 3. Unir los nodos agente

En cada máquina que vaya a actuar como worker, ejecuta el mismo script pasando la URL del servidor y el token obtenido en el paso anterior:

```bash
curl -sfL https://get.k3s.io | \
  K3S_URL=https://k3s-server-01:6443 \
  K3S_TOKEN=<token-del-servidor> \
  sh -
```

Sustituye `k3s-server-01` por la IP o el hostname real del nodo servidor accesible desde los agentes.

### 4. Verificar que el clúster quedó operativo

Desde el nodo servidor (o desde cualquier máquina con el kubeconfig configurado), confirma que todos los nodos aparecen y están en estado `Ready`:

```bash
sudo k3s kubectl get nodes -o wide
```

Debe listar el servidor y cada agente unido, con su rol y versión de Kubernetes. Si un agente no aparece tras un par de minutos, revisa que los puertos 6443/TCP y 8472/UDP estén abiertos entre ambas máquinas y que el token copiado no tenga saltos de línea de más.

### 5. Configurar kubectl fuera del servidor (opcional)

Para gestionar el clúster desde tu portátil en lugar de entrar por SSH cada vez, copia el kubeconfig y sustituye la IP local por la del servidor:

```bash
scp root@k3s-server-01:/etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i 's/127.0.0.1/k3s-server-01/' ~/.kube/config
kubectl get nodes
```

```
1. Instalar servidor (get.k3s.io)
      │
      ▼
2. Guardar node-token de /var/lib/rancher/k3s/server/node-token
      │
      ▼
3. Unir agentes con K3S_URL + K3S_TOKEN
      │
      ▼
4. Verificar con kubectl get nodes -o wide
      │
      ├── todos los nodos en Ready  → desplegar manifiestos
      └── algún nodo ausente        → revisar puertos 6443/8472 y el token
```

## Desplegar una aplicación de ejemplo

Con el clúster operativo, un `Deployment` y un `Service` básicos son suficientes para probar que todo funciona de extremo a extremo:

```yaml
# demo-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-demo
  template:
    metadata:
      labels:
        app: nginx-demo
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-demo
spec:
  selector:
    app: nginx-demo
  ports:
    - port: 80
      targetPort: 80
```

Aplícalo con:

```bash
kubectl apply -f demo-app.yaml
kubectl get pods -o wide
kubectl get svc nginx-demo
```

Como K3s trae Traefik activo por defecto, basta con añadir un recurso `Ingress` estándar para exponer el servicio con un nombre de host, sin instalar nada adicional:

```yaml
# demo-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-demo
spec:
  rules:
    - host: nginx-demo.homelab.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-demo
                port:
                  number: 80
```

```bash
kubectl apply -f demo-ingress.yaml
kubectl get ingress
```

Traefik quedará escuchando en los puertos 80/443 del nodo que lo ejecute y enrutará las peticiones por el `Host` indicado hacia el `Service`.

> [!TIP]
> Si prefieres usar tu propio ingress controller (por ejemplo, para uniformar con otro clúster que no sea K3s), puedes desactivar los componentes por defecto en la instalación del servidor con `curl -sfL https://get.k3s.io | sh -s - server --disable traefik --disable servicelb`.

## Gestión básica del día a día

Algunos comandos que usarás con frecuencia una vez el clúster está en marcha:

```bash
kubectl get pods --all-namespaces      # estado de todos los pods del clúster
kubectl logs -f deploy/nginx-demo      # logs en streaming de un deployment
kubectl describe node k3s-agent-01     # detalle de recursos y eventos de un nodo
kubectl delete -f demo-app.yaml        # eliminar los recursos desplegados
```

Para inspeccionar contenedores a nivel más bajo (equivalente a `docker ps`/`docker inspect` pero para el runtime containerd que usa K3s), el instalador deja disponibles `crictl` y `ctr`:

```bash
sudo k3s crictl ps
sudo k3s ctr images ls
```

## Alta disponibilidad, en breve

El ejemplo anterior usa un único nodo servidor con SQLite, válido para la inmensa mayoría de homelabs. Si más adelante quieres tolerar la caída de ese nodo, K3s soporta un modo de alta disponibilidad con **etcd embebido**, arrancando el primer servidor con el flag `--cluster-init` y uniendo servidores adicionales apuntando a él — a partir de ese momento el datastore deja de ser SQLite y pasa a ser un clúster etcd gestionado por el propio K3s. Es un salto de complejidad real (mínimo tres nodos servidor para quórum), así que solo tiene sentido si el homelab ya tiene ese nivel de disponibilidad en el resto de la infraestructura.

## Desinstalar el clúster

Cada nodo recibe su propio script de desinstalación durante la instalación:

```bash
# En el nodo servidor
sudo /usr/local/bin/k3s-uninstall.sh

# En cada nodo agente
sudo /usr/local/bin/k3s-agent-uninstall.sh
```

> [!CAUTION]
> El script de desinstalación detiene K3s, borra el datastore local, los volúmenes persistentes locales y toda la configuración del nodo. No hay confirmación intermedia ni forma de deshacerlo: si tienes datos en `PersistentVolume` de tipo local sin copia externa, se pierden. Haz una copia de lo que necesites conservar antes de ejecutarlo, y ten en cuenta que no toca datos guardados en datastores externos (etcd externo, RDS, etc.) — esos hay que limpiarlos aparte si corresponde.

## Siguiente paso

K3s no sustituye a Docker, Podman, Proxmox ni Incus/LXC — se apoya en todos ellos, cada uno en su capa: Docker o Podman para construir tus imágenes, Proxmox para las VMs que harán de nodos, y K3s para decidir en cuál de esas VMs corre cada contenedor y mantenerlo vivo. Empieza con un servidor y un par de agentes, valida el flujo completo con una app sencilla como la de este artículo, y añade nodos o alta disponibilidad solo cuando el homelab realmente lo demande.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
