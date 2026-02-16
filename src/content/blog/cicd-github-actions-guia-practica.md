---
title: "CI/CD con GitHub Actions: guía práctica"
description: "Aprende a configurar pipelines de integración y despliegue continuo con GitHub Actions: workflows, jobs, secrets y ejemplos reales para automatizar tu infraestructura."
author: "antonio"
pubDate: 2026-02-16
category: "Software"
tags: ["ci-cd", "github-actions", "devops", "automatizacion"]
image: "/images/soft-cicd.jpg"
draft: false
---

## Por qué CI/CD importa si administras servidores

Si alguna vez has desplegado a producción un viernes a las seis de la tarde con un `scp` manual y una plegaria, sabes exactamente por qué necesitas CI/CD. La integración continua (CI) y el despliegue continuo (CD) eliminan los pasos manuales que introducen errores humanos, y convierten cada cambio en tu repositorio en un proceso predecible y repetible.

Para un sysadmin, esto significa dejar de ser el cuello de botella. En lugar de que alguien te pida "sube esto al servidor", el pipeline se encarga automáticamente cada vez que se hace push a la rama correcta. Tú defines las reglas una vez y el sistema las ejecuta siempre igual.

GitHub Actions es la herramienta de CI/CD integrada en GitHub. No necesitas montar un Jenkins, ni mantener un servidor de Drone CI, ni configurar runners externos (aunque puedes). Todo vive en tu repositorio, se configura con archivos YAML y se ejecuta en máquinas virtuales que GitHub provisiona bajo demanda.

## Requisitos previos

Antes de empezar, asegúrate de tener lo siguiente:

- Una cuenta de GitHub (gratuita, los repos públicos tienen minutos ilimitados de Actions).
- Un repositorio con algo desplegable: un sitio estático, una aplicación, scripts de configuración, lo que sea.
- Conocimientos básicos de YAML (si sabes escribir un `docker-compose.yml`, ya estás listo).
- Acceso a un servidor remoto vía SSH si quieres seguir el ejemplo de despliegue (opcional).
- `git` instalado en tu máquina local.

## Anatomía de un workflow

Los workflows de GitHub Actions se definen en archivos YAML dentro del directorio `.github/workflows/` de tu repositorio. Un workflow tiene tres niveles jerárquicos: el evento que lo dispara, los jobs que ejecuta y los steps dentro de cada job.

Veamos la estructura básica:

```yaml
name: Mi primer workflow

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Clonar repositorio
        uses: actions/checkout@v4

      - name: Mostrar contenido
        run: ls -la
```

Esto es todo lo que necesitas para un workflow funcional. Vamos a desmenuzar cada parte.

### Triggers: el bloque `on`

El bloque `on` define cuándo se ejecuta el workflow. Los triggers más útiles para un sysadmin son:

```yaml
on:
  # Cada push a main o develop
  push:
    branches: [main, develop]

  # Cada pull request hacia main
  pull_request:
    branches: [main]

  # Programado (cron): cada día a las 3:00 UTC
  schedule:
    - cron: '0 3 * * *'

  # Manual desde la interfaz de GitHub
  workflow_dispatch:
```

El trigger `schedule` es oro puro para tareas de sysadmin: renovar certificados, ejecutar backups, lanzar escaneos de seguridad o actualizar dependencias de forma periódica. La sintaxis cron es la misma que ya conoces de `crontab`.

El trigger `workflow_dispatch` te permite ejecutar el workflow manualmente desde la pestaña Actions del repositorio, perfecto para despliegues que necesitas controlar a mano.

### Jobs y steps

Un job es un conjunto de pasos que se ejecutan en la misma máquina virtual. Por defecto, los jobs se ejecutan en paralelo. Si necesitas que uno espere a otro, usas `needs`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Ejecutar tests
        run: npm test

  deploy:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Desplegar
        run: echo "Desplegando..."
```

En este ejemplo, `deploy` solo se ejecuta si `test` termina con éxito. Cada step puede ser una acción reutilizable (con `uses`) o un comando de shell (con `run`).

El campo `runs-on` define el entorno. Tienes disponibles `ubuntu-latest`, `windows-latest` y `macos-latest`. Para la mayoría de tareas de infraestructura, `ubuntu-latest` es lo que vas a usar.

## Gestión de secrets

Nunca metas contraseñas, tokens ni claves SSH directamente en tus archivos YAML. GitHub ofrece secrets cifrados que puedes configurar en Settings > Secrets and variables > Actions dentro de tu repositorio.

Para crear un secret:

1. Ve a tu repositorio en GitHub.
2. Settings > Secrets and variables > Actions.
3. Haz clic en "New repository secret".
4. Dale un nombre (por ejemplo `SERVER_SSH_KEY`) y pega el valor.

Dentro del workflow, accedes a los secrets así:

```yaml
steps:
  - name: Desplegar por SSH
    env:
      SSH_KEY: ${{ secrets.SERVER_SSH_KEY }}
      SERVER_HOST: ${{ secrets.SERVER_HOST }}
    run: |
      echo "$SSH_KEY" > /tmp/deploy_key
      chmod 600 /tmp/deploy_key
      ssh -i /tmp/deploy_key -o StrictHostKeyChecking=no user@$SERVER_HOST "cd /var/www && git pull"
```

Los secrets nunca se muestran en los logs. Si un step intenta imprimirlos, GitHub los enmascara con `***`. Aun así, ten cuidado con comandos que podrían exponer variables de entorno de forma indirecta.

## Matrix builds

La estrategia `matrix` te permite ejecutar el mismo job con diferentes combinaciones de parámetros. Esto es especialmente útil para probar en múltiples versiones o entornos:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, ubuntu-22.04]
    steps:
      - uses: actions/checkout@v4

      - name: Configurar Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}

      - run: npm ci
      - run: npm test
```

Este workflow genera seis ejecuciones paralelas: tres versiones de Node por dos sistemas operativos. Si administras infraestructura con múltiples entornos, la matrix te garantiza que todo funciona en cada uno antes de desplegar.

## Ejemplos prácticos

### Linting y validación en cada pull request

Este workflow ejecuta un linter cada vez que alguien abre o actualiza un pull request. Es la primera línea de defensa para mantener la calidad del código:

```yaml
name: Lint

on:
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Instalar dependencias
        run: npm ci

      - name: Ejecutar ESLint
        run: npx eslint . --max-warnings 0

      - name: Verificar formato
        run: npx prettier --check .
```

Con `--max-warnings 0`, el workflow falla si hay cualquier advertencia. Esto fuerza a que cada PR cumpla con los estándares antes de hacer merge.

### Desplegar un sitio estático

Si tienes un sitio generado con Astro, Hugo, Jekyll o cualquier generador estático, puedes desplegarlo automáticamente a GitHub Pages:

```yaml
name: Deploy sitio estático

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Instalar dependencias
        run: npm ci

      - name: Build
        run: npm run build

      - name: Subir artefacto
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Desplegar a GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

El bloque `permissions` es necesario porque GitHub Pages usa tokens OIDC para la autenticación. El job `build` genera el sitio y lo sube como artefacto, y el job `deploy` lo publica.

### Despliegue por SSH a un servidor propio

Este es el escenario clásico del sysadmin: tienes un VPS o servidor dedicado y quieres desplegar automáticamente cuando haces push a `main`:

```yaml
name: Deploy a servidor

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configurar clave SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H ${{ secrets.SERVER_HOST }} >> ~/.ssh/known_hosts

      - name: Desplegar
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} << 'ENDSSH'
            cd /var/www/mi-aplicacion
            git pull origin main
            npm ci --production
            pm2 restart mi-app
          ENDSSH
```

Para que esto funcione necesitas tres secrets configurados: `SSH_PRIVATE_KEY` (la clave privada), `SERVER_HOST` (IP o dominio del servidor) y `SERVER_USER` (el usuario SSH). La clave pública correspondiente debe estar en el `~/.ssh/authorized_keys` del servidor.

El bloque `ssh-keyscan` previene el error de host desconocido la primera vez que se conecta. El heredoc `<< 'ENDSSH'` ejecuta todos los comandos en el servidor remoto en una sola sesión SSH.

## Consejos para el día a día

**Cachea dependencias.** Si tu workflow instala paquetes con npm, pip o apt, usa el action `actions/cache@v4` para no descargar todo desde cero en cada ejecución:

```yaml
- name: Cache de node_modules
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

**Usa `concurrency` para evitar despliegues simultáneos.** Si dos pushes llegan casi al mismo tiempo, no quieres que ambos desplieguen a la vez:

```yaml
concurrency:
  group: deploy-production
  cancel-in-progress: true
```

**Revisa los logs.** Cuando un workflow falla, la pestaña Actions te muestra los logs de cada step. La mayoría de problemas son permisos, versiones incorrectas o secrets mal configurados.

**Empieza simple.** No intentes cubrir todos los casos desde el primer día. Un workflow que hace checkout, build y deploy ya te ahorra horas de trabajo manual. Puedes ir añadiendo tests, matrix builds y notificaciones después.

## Siguiente paso

Ya tienes las bases para automatizar cualquier flujo con GitHub Actions. El siguiente paso natural es explorar los self-hosted runners: máquinas que tú controlas (un servidor de tu red, una Raspberry Pi, una VM) donde se ejecutan los workflows en lugar de en la infraestructura de GitHub. Esto te da acceso a hardware específico, redes internas y elimina los límites de minutos gratuitos. Consulta la documentación oficial de GitHub sobre self-hosted runners y prepárate para llevar tu automatización al siguiente nivel.
