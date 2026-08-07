---
title: '¿Por qué este blog?'
description: 'Presentación del blog: qué encontrarás, el stack técnico (Astro, MDX) y por qué un sysadmin decidió escribir sobre Linux e infraestructura.'
author: 'antonio'
pubDate: 2026-02-20
updatedDate: 2026-08-07
category: 'Opinión'
tags: ['Staff']
image: '../../assets/images/por-que-este-blog.jpg'
draft: false
---

## ¿Qué te hemos hecho para merecer esto?

Llevaba tiempo con la idea en la cabeza de tener un sitio donde soltar todo el conocimiento que voy acumulando con los años. No es que sea la biblioteca de Alejandría, pero prefiero compartirlo a dejarlo pudriéndose en notas privadas que no vuelvo a abrir jamás.

Así que aquí estamos. Si esto termina siendo útil para alguien, ya habrá merecido la pena. Y si no… bueno, al menos me sirve de chuleta personal 😅.

---

## ¿Qué vas a encontrar en este barrizal?

Material útil para el día a día. Sin postureo. Sin vender humo.

Principalmente:

- Tutoriales prácticos
- Cheat Sheets
- Explicaciones técnicas aterrizadas a la vida real

La mayoría de artículos salen de algo que hemos montado o roto de verdad en nuestro propio homelab o en producción, no de reescribir la documentación oficial con otras palabras. Si un comando aparece en un artículo, lo hemos ejecutado; si un artículo dice "esto falla si haces X", es porque a alguno de los dos le ha fallado por hacer X. Eso también significa que no vas a encontrar aquí "los 10 mejores frameworks de 2026" ni listados genéricos hechos para posicionar: si un tema no lo hemos tocado con las manos, no escribimos sobre él.

También habrá artículos con ayuda de IA. No vamos a hacer como si eso no existiera. Pero todo lo que se publique estará revisado y validado antes. Y cuando un artículo tenga ayuda fuerte de IA, estará indicado claramente así:

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.

Lo que la IA no hace aquí es inventar el contenido: la usamos para investigar más rápido, estructurar un borrador o pulir redacción, pero cada comando, cada configuración y cada "esto se rompe si..." pasa antes por un terminal real. Si algo no lo hemos verificado nosotros, no se publica tal cual.

La idea es simple: si algo está aquí, debería servirte para algo.

---

## ¿Por qué está tan “mal hecho” este blog?

Porque el día tiene 24 horas y yo no soy desarrollador web.

No tengo tiempo para convertirme en frontend engineer ni presupuesto para contratar uno. Así que he tirado de herramientas que me permiten construir algo funcional sin hipotecar mi vida.

El objetivo del stack es claro: simple, barato y mantenible por una sola persona.

El stack tecnológico es el siguiente:

| Herramienta | Uso                                |
| ----------- | ---------------------------------- |
| Astro 7     | Framework web estático             |
| MDX         | Markdown con componentes           |
| Pagefind    | Búsqueda estática (~15KB)          |
| Shiki       | Resaltado de sintaxis              |
| giscus      | Comentarios vía GitHub Discussions |
| Claude      | Asistencia en diseño y desarrollo  |

---

## ¿Por qué Astro y no otro?

Por sensaciones. Sí, sensaciones.

A veces vas leyendo cosas en foros, viendo contenido técnico en YouTube, streams en Twitch, artículos de desarrolladores… y se te queda el runrún.

Tenía ganas de probar Astro y ver qué tal funcionaba en un proyecto real.

El blog está alojado en GitHub y desplegado automáticamente usando Cloudflare Pages.

Flujo real:

1. Escribo en Markdown
2. Commit
3. Push
4. Cloudflare compila y publica

En un par de minutos está online sin tocar nada más. Para alguien que no vive del desarrollo web, esto es oro.

---

### ¿Por qué Cloudflare Pages y no GitHub Pages?

Porque ya tenía el dominio gestionado ahí y además me da:

- Métricas
- Routing
- Seguridad
- Gestión DNS y enrutamiento de correo
- Y más cosas que iré usando poco a poco

---

## ¿Quiénes sois y dónde está mi cartera?

Somos gente que disfruta cacharreando con tecnología.

Aquí entra de todo:

- Linux
- Redes y telecomunicaciones
- Fibra óptica
- Infraestructura
- Desarrollo web
- Open Source

Ahora mismo el blog lo escribimos dos personas. Yo llevo unos años currando en consultoría y telecomunicaciones, con temporadas eminentemente en NOC monitorizando infraestructuras ajenas, y por el camino he ido sacándome certificaciones de redes y cloud porque me gusta entender el porqué de las cosas, no solo el cómo. Alois viene del mismo mundo — sistemas, redes, virtualización — con más querencia por la automatización y por dejar la infraestructura montada de forma que no haya que tocarla cada dos semanas. Ninguno de los dos vive de este blog ni pretende vivir de él: escribimos fuera de horario, con la misma infraestructura que usamos en el día a día, no con un laboratorio de postureo montado solo para hacer capturas de pantalla bonitas.

No somos una empresa. No somos gurús. Solo gente que prueba cosas, las rompe, las arregla, y cuenta lo que aprende por el camino.

---

## ¿Puedo unirme al código fuente?

Si has llegado hasta aquí sin cerrar la pestaña, ya eres de los nuestros.

Si quieres colaborar:
Haz un pull request con tu artículo.
Se revisa.
Si encaja → se publica.

Fácil, sin ceremonias.

---

Si algún día un artículo de este blog te ahorra 30 minutos de Google, esto ya habrá merecido la pena.
