---
title: 'Vim: por qué merece la pena frente a nano'
description: 'Vim parece complicado pero no lo es: aprende a salir, moverte y editar con lo mínimo imprescindible, sin miedo y sin memorizar todo de golpe.'
author: 'antonio'
pubDate: 2026-08-01T13:00:00
category: 'Software'
tags: ['Terminal', 'Sysadmin', 'Cheatsheet', 'Linux']
image: '../../assets/images/soft-vim.jpg'
draft: false
---

Vim tiene fama de ser imposible de usar, y esa fama viene casi siempre de la misma experiencia: alguien lo abre por primera vez, escribe algo, y no consigue salir. Es una sensación horrible y es la razón número uno por la que mucha gente se queda con `nano` para siempre. Así que vamos a resolver eso ya, en la primera sección, antes de explicar nada más.

## Lo primero de todo: cómo salir

Si en algún momento te quedas "atrapado" en Vim, haz esto:

1. Pulsa `Esc` (puede que tengas que pulsarlo dos veces, no pasa nada).
2. Escribe `:q!` y pulsa `Enter`. Esto sale sin guardar nada.

Eso es todo. Ya no te puedes quedar encerrado. Guárdate esta combinación —`Esc`, `:q!`, `Enter`— y el resto del artículo lo puedes leer tranquilo, sabiendo que siempre tienes una salida.

> [!TIP]
> Si además quieres guardar los cambios antes de salir, es `:wq` en vez de `:q!`. Y si prefieres no escribir los dos puntos, `ZZ` (mayúsculas, sin `Enter`) hace lo mismo que `:x`: guarda y sale, pero solo escribe el archivo si hay cambios sin guardar.

## Y si la lías, deshazlo

La otra mitad del miedo a Vim no es "no sé salir", es "voy a romper algo y no voy a poder arreglarlo". Tampoco es verdad: `u` deshace el último cambio, igual que `Ctrl+Z` en cualquier otro editor, y puedes pulsarlo varias veces seguidas para deshacer varios pasos atrás. Si te pasas de frenada, `Ctrl+r` rehace lo que acabas de deshacer.

No hay forma de "romper" un archivo en Vim que `u` no pueda arreglar. Prueba a borrar una línea entera con `dd` ahora mismo y deshazla con `u` — así lo compruebas tú mismo antes de seguir leyendo.

## Vale, ¿y por qué merece la pena?

No hace falta que te convenza nadie de usar Vim a la fuerza: `nano` es perfectamente válido para tocar un archivo de vez en cuando. La razón práctica para aprender Vim es otra: `vi` (su base) es un utilitario exigido por POSIX, así que cualquier sistema Unix lo trae sí o sí. `nano` no forma parte de ese estándar y a veces, sencillamente, no está.

Lo notarás el día que entres en un contenedor mínimo, un sistema de rescate o un servidor recién instalado y `nano: command not found` sea lo único que consigas. `vi` va a estar ahí. Es la misma razón por la que BusyBox —el conjunto de utilidades que usan Alpine y muchos sistemas embebidos— trae un applet `vi`, pero no trae `nano`: cuando solo hay sitio para un editor, se elige el que nunca falta.

Lo que vas a usar en la práctica es Vim ("Vi IMproved"), la evolución de vi que trae instalada casi cualquier distro moderna, o a un `apt install` de distancia.

## Los "modos" no son tan raros como suenan

Lo que más descoloca al venir de `nano` es que Vim tiene modos: el mismo teclado hace cosas distintas según en qué modo estés. Suena raro dicho así, pero en la práctica solo necesitas saber que hay dos:

- **Modo normal** — el modo en el que abres Vim. Aquí las teclas son comandos: moverte, borrar, copiar. No escribes texto directamente.
- **Modo inserción** — aquí sí escribes como en cualquier editor normal. Entras con `i`, sales con `Esc` (y vuelves al modo normal).

Eso es literalmente todo lo que necesitas entender para empezar: `i` para escribir, `Esc` para dejar de escribir, `:q!` para salir. Con eso ya puedes usar Vim como un `nano` algo más incómodo. Todo lo que viene ahora es opcional, y es lo que lo convierte en algo realmente más rápido.

## Un primer ejemplo, sin prisa

Abre cualquier archivo de texto que no te importe romper con `vim archivo.txt` y prueba esto:

1. Comprueba que estás en modo normal (pulsa `Esc` si tienes dudas).
2. Coloca el cursor al principio de una palabra.
3. Pulsa `d` y luego `w`.

La palabra desaparece. No has roto nada raro: acabas de combinar un **operador** (`d`, de "delete") con un **motion** (`w`, de "word", hasta el final de la palabra). Esa combinación —operador más motion— es toda la idea detrás de Vim. Una vez la ves funcionar una vez, el resto son variaciones del mismo patrón, no cosas nuevas que memorizar.

## Más combinaciones, cuando te apetezca ir más allá

No hace falta aprenderlas todas a la vez. Ve probando cuando te acuerdes:

- `c$` — cambia (**c**hange) hasta el final de la línea (`$`): borra el resto de la línea y te deja escribiendo.
- `di"` — borra (**d**elete) dentro (**i**nside) de las comillas: da igual la longitud del texto entre `"` y `"`, no hay que seleccionar nada a mano.
- `yy` — copia (**y**ank) la línea completa.

Esto es justo lo que en `nano` no existe: ahí borras carácter a carácter o línea a línea con teclas fijas. En Vim, `di"` funciona igual da igual dónde estés dentro de la línea.

Cuando te sientas cómodo con lo anterior, hay un comando que lo multiplica todo: `.` repite el último cambio. Borra una palabra con `dw`, mueve el cursor a otra palabra, pulsa `.`, y se repite la misma acción. No hay prisa por llegar hasta aquí — sigue usando solo `i`/`Esc`/`dw` el tiempo que necesites primero.

## La chuleta completa: combina lo que necesites

Esto no es una lista para memorizar de un tirón — es una referencia. Guárdala y vuelve cuando te encuentres pensando "seguro que hay una forma más rápida de hacer esto".

La idea sigue siendo la misma que con `dw`: un **operador** (qué hacer) más un **motion** (dónde hacerlo). Estos son los que más vas a usar de cada tipo.

**Operadores** (el "qué"):

| Operador    | Significa                                               | Ejemplo                                      |
| ----------- | ------------------------------------------------------- | -------------------------------------------- |
| `d`         | borrar (**d**elete)                                     | `dw` — borra una palabra                     |
| `c`         | cambiar (**c**hange): borra y te deja en modo inserción | `c$` — cambia hasta el final de la línea     |
| `y`         | copiar (**y**ank)                                       | `yy` — copia la línea                        |
| `>` / `<`   | indentar a la derecha / izquierda                       | `>>` — indenta la línea actual               |
| `gU` / `gu` | pasar a mayúsculas / minúsculas                         | `gUiw` — pon en mayúsculas la palabra actual |

**Motions** (el "dónde"):

| Motion              | Significa                                           | Ejemplo                                      |
| ------------------- | --------------------------------------------------- | -------------------------------------------- |
| `w` / `b`           | siguiente palabra / palabra anterior                | `dw`, `db`                                   |
| `0` / `^`           | inicio absoluto de línea / primer carácter no vacío | `d0`, `d^`                                   |
| `$`                 | final de la línea                                   | `c$`                                         |
| `gg` / `G`          | inicio / final del archivo                          | `dgg`, `dG`                                  |
| `f{car}` / `t{car}` | hasta el carácter `{car}` (inclusive / justo antes) | `dt,` — borra hasta antes de la próxima coma |
| `i"` / `i(` / `ip`  | dentro de comillas / paréntesis / párrafo           | `di"`, `ci(`, `dip`                          |
| `{n}G`              | ir directamente a la línea `{n}`                    | `42G` — salta a la línea 42                  |

Combinando tabla con tabla salen cosas como `yi(` (copia el contenido entre paréntesis), `cip` (reescribe un párrafo entero de golpe) o `d0` (borra desde el cursor hasta el principio de la línea). No hace falta que las pruebes todas ahora — la próxima vez que te encuentres haciendo algo a mano con `nano`, vuelve aquí y busca si hay una combinación para ello.

`{n}G` es especialmente útil como sysadmin: cuando `nginx -t` o `sshd -t` te devuelven algo como "error en la línea 42", no hace falta que la busques a ojo — abre el archivo y ve directo con `42G`.

Casi todo lo anterior también acepta un número delante, que repite la acción esa cantidad de veces: `3dw` borra 3 palabras, `5dd` borra 5 líneas, `2yy` copia 2 líneas. El número siempre va antes del operador o del motion, nunca en medio.

> [!CAUTION]
> Ya que estamos con `gg` y `G`: `ggdG` (ir al principio, borrar hasta el final) vacía el archivo entero de golpe. Es la típica anécdota que circula sobre Vim, y es real — pero ahora ya sabes por qué pasa, así que no te va a pillar por sorpresa.

## Buscar y reemplazar en todo el archivo

Para cambios puntuales, `/` busca hacia delante y `?` hacia atrás; `n`/`N` repiten la búsqueda en la misma dirección o en la contraria.

Para sustituir en todo el archivo de una vez:

```text
:%s/textoviejo/textonuevo/g
```

`%` significa "todo el archivo", `s` es "substitute" y la `g` final aplica el cambio a todas las coincidencias de cada línea, no solo a la primera.

## Modo visual, si prefieres ver la selección

Si memorizar un operador y un motion exactos no te convence todavía, no pasa nada: puedes seleccionar a la vista, como en cualquier editor, con el modo visual.

- `v` — selección por caracteres.
- `V` — selección por líneas completas.
- `Ctrl+v` — selección por bloque (columna), útil para editar varias líneas a la vez en la misma posición, por ejemplo para comentar un bloque de config añadiendo `#` al principio de cada línea.

Una vez seleccionado, cualquier operador actúa sobre lo resaltado: `d` borra, `y` copia. `Ctrl+v` en concreto no tiene equivalente directo en `nano`.

## Llévalo a las guías de este blog

Ya viste en la guía de [Git para sysadmins](/blog/git-control-versiones-sysadmins/) que se puede fijar `git config --global core.editor vim`, así que cada `git commit` sin `-m` te abre directamente en Vim. Y la próxima vez que sigas una guía de este blog con `sudo nano /etc/algo.conf` (WireGuard, Nextcloud, Pi-hole, Gitea...), puedes cambiarlo por `sudo vim /etc/algo.conf` sin que cambie nada más del procedimiento — y ya sabes cómo salir si algo no sale como esperabas.

Vim también encaja sin fricción dentro de un panel de [tmux](/blog/tmux-screen-multiplexores-terminal-sysadmins/), y su forma de moverse ha influido en otras herramientas de terminal: [btop](/blog/btop-monitor-recursos-terminal/) ofrece `vim_keys = true` como alternativa a las flechas precisamente porque mucha gente ya tiene esos movimientos en los dedos.

## Siguiente paso

Si te quedas solo con `i`, `Esc`, `:q!`/`:wq` y `u` para deshacer, ya puedes usar Vim sin miedo cuando `nano` no esté disponible — y eso, por sí solo, ya vale la pena. El resto —`dw`, `di"`, el repeat `.`, los contadores, `42G`, `:%s///g`— lo vas incorporando cuando te apetezca, sin ninguna prisa. No hace falta memorizar nada de este artículo de golpe: vuelve cuando lo necesites, y en poco tiempo lo tendrás en los dedos sin pensarlo.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
