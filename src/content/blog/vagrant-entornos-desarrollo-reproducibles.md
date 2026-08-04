---
title: 'Vagrant: entornos de desarrollo reproducibles'
description: 'Aprende a usar Vagrant con libvirt o VirtualBox para crear y compartir entornos de desarrollo idénticos en segundos.'
author: 'antonio'
pubDate: 2026-02-06
updatedDate: 2026-07-27
category: 'Virtualización'
tags: ['Vagrant', 'Virtualización', 'DevOps', 'Automatización']
image: '../../assets/images/vagrant-dev.jpg'
draft: false
---

## El problema que resuelve Vagrant

¿Cuántas veces has escuchado "en mi máquina funciona"? Vagrant elimina ese problema. Es una herramienta de HashiCorp que permite definir entornos de desarrollo como código: un fichero de texto (Vagrantfile) describe la máquina virtual, su configuración y el software necesario. Cualquier miembro del equipo puede levantar un entorno idéntico con un solo comando.

A diferencia de un hipervisor tipo 1 como [Proxmox VE](/blog/proxmox-ve-hipervisor-casero/), Vagrant no es un hipervisor en sí mismo: trabaja sobre proveedores como VirtualBox, libvirt/KVM o VMware, abstrayendo las diferencias entre ellos para ofrecer un flujo de trabajo unificado.

## Instalación

### Instalar Vagrant

En distribuciones basadas en Debian:

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install vagrant -y
```

En Fedora/RHEL:

```bash
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://rpm.releases.hashicorp.com/fedora/hashicorp.repo
sudo dnf install vagrant -y
```

### Instalar un proveedor

Si usas libvirt (recomendado en Linux):

```bash
sudo apt install libvirt-daemon-system qemu-kvm -y
sudo apt install -y build-essential libvirt-dev libxslt-dev libxml2-dev zlib1g-dev ruby-dev pkg-config
vagrant plugin install vagrant-libvirt
```

Si prefieres VirtualBox, instálalo desde los repositorios de Oracle y Vagrant lo detectará automáticamente.

Verifica la instalación:

```bash
vagrant --version
```

## Estructura del Vagrantfile

El Vagrantfile es un fichero Ruby que define la configuración de la VM. Crea un proyecto nuevo:

```bash
mkdir mi-proyecto && cd mi-proyecto
vagrant init generic/debian12
```

Esto genera un Vagrantfile básico. Edítalo para ajustar los recursos:

```ruby
Vagrant.configure("2") do |config|
  config.vm.box = "generic/debian12"
  config.vm.hostname = "dev-server"

  config.vm.network "private_network", ip: "192.168.56.10"
  config.vm.network "forwarded_port", guest: 8080, host: 8080

  config.vm.provider "libvirt" do |lv|
    lv.memory = 2048
    lv.cpus = 2
  end

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 2048
    vb.cpus = 2
  end
end
```

Los parámetros clave:

- `config.vm.box`: imagen base de la VM (se descarga de Vagrant Cloud).
- `config.vm.network`: red privada con IP fija y reenvío de puertos.
- `config.vm.provider`: configuración específica de cada proveedor.

## Ciclo de vida básico

### Levantar la VM

```bash
vagrant up
```

La primera vez descarga la box y crea la VM. Las siguientes ejecuciones simplemente la arranca.

### Conectar por SSH

```bash
vagrant ssh
```

Accedes directamente a la VM sin necesidad de configurar claves SSH manualmente.

### Parar la VM

```bash
vagrant halt
```

Apaga la VM de forma limpia pero conserva el disco.

### Destruir la VM

```bash
vagrant destroy -f
```

Elimina la VM por completo. La próxima vez que ejecutes `vagrant up` se creará desde cero.

### Ver el estado

```bash
vagrant status
vagrant global-status
```

## Aprovisionamiento con shell scripts

Vagrant puede ejecutar scripts automáticamente al crear la VM. Añade esto al Vagrantfile:

```ruby
config.vm.provision "shell", inline: <<-SHELL
  apt-get update
  apt-get install -y nginx git curl
  systemctl enable --now nginx
SHELL
```

También puedes referenciar un script externo:

```ruby
config.vm.provision "shell", path: "scripts/setup.sh"
```

El aprovisionamiento se ejecuta solo en el primer `vagrant up`. Para forzar su ejecución posterior:

```bash
vagrant provision
```

Vagrant soporta otros provisioners como [Ansible](/blog/automatizar-servidores-ansible-primeros-pasos/), Puppet o Chef, pero los scripts de shell son la opción más directa para empezar.

## Entornos multi-máquina

Un solo Vagrantfile puede definir varias VMs. Esto es muy útil para simular arquitecturas completas (web + base de datos, por ejemplo):

```ruby
Vagrant.configure("2") do |config|
  config.vm.define "web" do |web|
    web.vm.box = "generic/debian12"
    web.vm.hostname = "web-server"
    web.vm.network "private_network", ip: "192.168.56.10"
    web.vm.provider "libvirt" do |lv|
      lv.memory = 1024
      lv.cpus = 1
    end
    web.vm.provision "shell", inline: "apt-get update && apt-get install -y nginx"
  end

  config.vm.define "db" do |db|
    db.vm.box = "generic/debian12"
    db.vm.hostname = "db-server"
    db.vm.network "private_network", ip: "192.168.56.11"
    db.vm.provider "libvirt" do |lv|
      lv.memory = 2048
      lv.cpus = 2
    end
    db.vm.provision "shell", inline: "apt-get update && apt-get install -y postgresql"
  end
end
```

```
Tu máquina (host)
   │
   │ red privada libvirt, 192.168.56.0/24
   │
   ├── web-server  192.168.56.10  → nginx
   └── db-server   192.168.56.11  → postgresql
```

Gestiona cada VM por separado:

```bash
vagrant up web
vagrant ssh db
vagrant halt web
```

## Compartir boxes

Si creas una configuración útil, puedes empaquetar la VM como una box reutilizable:

```bash
vagrant package --output mi-entorno.box
```

Otros miembros del equipo pueden importarla:

```bash
vagrant box add mi-entorno mi-entorno.box
```

También puedes publicar boxes en Vagrant Cloud para compartirlas con la comunidad o con tu equipo de forma privada.

## Comandos de referencia

```bash
vagrant init <box>       # inicializar proyecto con una box
vagrant up               # crear y arrancar VM
vagrant ssh              # conectar por SSH
vagrant halt             # apagar VM
vagrant destroy -f       # eliminar VM
vagrant provision        # re-ejecutar aprovisionamiento
vagrant status           # estado de las VMs
vagrant box list         # boxes descargadas localmente
vagrant package          # empaquetar VM como box
```

## Conclusión

Vagrant convierte la creación de entornos de desarrollo en un proceso predecible y repetible. Con un Vagrantfile versionado en [Git](/blog/git-control-versiones-sysadmins/), todos los miembros del equipo trabajan sobre la misma base. Combinado con aprovisionamiento automático, puedes tener un entorno completo funcionando en minutos.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
