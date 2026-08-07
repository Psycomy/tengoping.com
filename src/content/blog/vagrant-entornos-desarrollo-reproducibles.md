---
title: 'Vagrant: entornos de desarrollo reproducibles'
description: 'Vagrant con libvirt o VirtualBox: carpetas sincronizadas, snapshots, aprovisionamiento con Ansible y reload vs provision.'
author: 'antonio'
pubDate: 2026-02-06
updatedDate: 2026-08-05
category: 'Virtualización'
tags: ['Vagrant', 'Virtualización', 'DevOps', 'Automatización']
image: '../../assets/images/vagrant-dev.jpg'
draft: false
---

## El problema que resuelve Vagrant

¿Cuántas veces has escuchado "en mi máquina funciona"? Vagrant elimina ese problema. Es una herramienta de HashiCorp que permite definir entornos de desarrollo como código: un fichero de texto (Vagrantfile) describe la máquina virtual, su configuración y el software necesario. Cualquier miembro del equipo puede levantar un entorno idéntico con un solo comando.

A diferencia de un hipervisor tipo 1 como [Proxmox VE](/blog/proxmox-ve-hipervisor-casero/), Vagrant no es un hipervisor en sí mismo: trabaja sobre proveedores como VirtualBox, [libvirt/KVM](/blog/kvm-libvirt-virtualizacion-nativa-linux/) o VMware, abstrayendo las diferencias entre ellos para ofrecer un flujo de trabajo unificado.

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

## Carpetas sincronizadas

Por defecto, Vagrant monta el directorio donde vive el Vagrantfile dentro de la VM en `/vagrant` — así puedes editar el código con tu editor habitual en el host y ejecutarlo dentro de la VM sin copiar nada a mano. Puedes definir carpetas adicionales o cambiar el mecanismo de sincronización:

```ruby
config.vm.synced_folder "./app", "/var/www/app", type: "nfs"
```

El parámetro `type` importa más de lo que parece:

- **VirtualBox** usa por defecto sus propias shared folders (`vboxsf`), que funcionan sin configuración extra pero son notablemente lentas con muchos archivos pequeños (por ejemplo, un `node_modules`).
- **libvirt** puede elegir entre NFS y rsync de forma no determinista si no se especifica `type` — para evitar sorpresas, indícalo siempre de forma explícita en Vagrantfiles que usen este proveedor.
- **rsync** sincroniza en una sola dirección (host → VM) y solo al arrancar o con `vagrant rsync`, útil cuando NFS no es viable en la red del host, pero no ves los cambios hechos dentro de la VM reflejados de vuelta.

## Snapshots: puntos de restauración rápidos

A diferencia de `vagrant halt`/`vagrant up`, que conservan el disco tal cual, un snapshot te permite volver a un estado exacto anterior sin rehacer el aprovisionamiento — útil antes de probar un cambio arriesgado dentro de la VM:

```bash
vagrant snapshot save antes-de-probar
# ... pruebas algo que podría romper la VM ...
vagrant snapshot restore antes-de-probar
vagrant snapshot list
```

> [!TIP]
> `vagrant snapshot push` guarda un snapshot y lo apila; `vagrant snapshot pop` restaura el último y lo elimina de la pila. Es cómodo para un solo nivel de "prueba y deshaz", pero no mezcles `push`/`pop` con `save`/`restore` en la misma VM — usar ambos pares a la vez es una fuente de confusión que el propio Vagrant desaconseja.

## Aprovisionamiento con Ansible

Si ya tienes o vas a escribir un playbook de [Ansible](/blog/automatizar-servidores-ansible-primeros-pasos/), Vagrant puede usarlo como provisioner en vez de un script de shell — muy útil para probar el playbook contra una VM desechable antes de tocar un servidor real:

```ruby
config.vm.provision "ansible" do |ansible|
  ansible.playbook = "playbook.yml"
end
```

Vagrant genera el inventario automáticamente a partir de las VMs definidas en el Vagrantfile, así que no hace falta mantener uno a mano para este caso de uso.

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

Vagrant soporta también Puppet o Chef como provisioners, pero entre shell y Ansible cubres la gran mayoría de casos de uso reales.

### Cambios en el Vagrantfile: reload, no provision

Modificar el Vagrantfile (por ejemplo, la memoria asignada o el reenvío de puertos) no se aplica solo. `vagrant provision` re-ejecuta el aprovisionamiento, pero no relee cambios de red o de proveedor; para eso hace falta `vagrant reload`, que equivale a un `halt` seguido de un `up`:

```bash
vagrant reload              # aplica cambios de configuración, no re-aprovisiona
vagrant reload --provision  # aplica cambios de configuración Y re-ejecuta el aprovisionamiento
```

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
vagrant reload           # aplicar cambios del Vagrantfile (halt + up)
vagrant destroy -f       # eliminar VM
vagrant provision        # re-ejecutar aprovisionamiento
vagrant snapshot save x  # guardar un snapshot
vagrant snapshot restore x  # volver a un snapshot
vagrant status           # estado de las VMs
vagrant box list         # boxes descargadas localmente
vagrant package          # empaquetar VM como box
```

## Conclusión

Vagrant convierte la creación de entornos de desarrollo en un proceso predecible y repetible. Con un Vagrantfile versionado en [Git](/blog/git-control-versiones-sysadmins/), todos los miembros del equipo trabajan sobre la misma base. Combinado con aprovisionamiento automático, puedes tener un entorno completo funcionando en minutos.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
