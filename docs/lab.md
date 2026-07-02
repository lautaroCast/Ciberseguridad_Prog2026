# Alcance legal y ético del laboratorio

## Declaración de alcance

VulnScan Platform está diseñada para escanear **exclusivamente** las
aplicaciones definidas como servicios en `docker-compose.yml` dentro de la
red Docker `lab-network`, desplegadas localmente por el propio usuario. El
sistema **no está diseñado, ni autorizado, ni debe usarse** para interactuar
con:

- Sistemas públicos o de terceros, con o sin autorización aparente.
- Cualquier host fuera de `lab-network`, incluida la red local del usuario o
  internet.
- Objetivos que no hayan sido explícitamente registrados como target de
  laboratorio.

Escanear sistemas sin autorización explícita del propietario es ilegal en la
gran mayoría de las jurisdicciones (en Argentina, entre otras normas,
puede encuadrar en figuras del Código Penal sobre acceso indebido a sistemas
informáticos — Ley 26.388). Este proyecto existe para practicar y demostrar
estas técnicas de forma segura y legal, no para saltarse esa barrera.

## Por qué la arquitectura hace esto cumplible, no solo "una regla"

1. **Red segmentada (`lab-network`)**: el resto de la plataforma (frontend,
   n8n, Backend, base de datos) simplemente no tiene ruta hacia
   `lab-network` — solo el Scanner Service (Módulo 4) se conecta a la vez a
   `app-network` y a `lab-network`. Ningún otro componente puede alcanzar
   los targets del laboratorio ni por error.

   Se evaluó marcar `lab-network` como `internal: true` para además impedir
   que los propios contenedores del laboratorio tengan salida a internet,
   pero se descartó: Docker omite silenciosamente la publicación de puertos
   hacia el host (`ports:`) para contenedores cuya única red es `internal`
   (comprobado de forma empírica al construir este módulo — `docker port`
   no devolvía nada pese a que `docker compose config` mostraba el mapeo
   correcto), lo que dejaba Juice Shop y DVWA inalcanzables desde el
   navegador del host. La garantía real de que la plataforma nunca escanea
   nada fuera del laboratorio no depende de la topología de red, sino de la
   whitelist aplicada por el Backend (punto 2 más abajo).
2. **Whitelist en base de datos**: la tabla `targets` (Módulo 1) tiene la
   columna `is_lab_target`. El Backend API (Módulo 3) rechazará cualquier
   intento de registrar o escanear un host que no forme parte del
   laboratorio declarado — el pipeline nunca acepta un target arbitrario
   ingresado a mano.
3. **Todo el laboratorio es reproducible y descartable**: `docker compose
   down -v` elimina por completo el estado de los targets vulnerables. No
   hay dependencia de infraestructura persistente ni compartida.

## Aplicaciones incluidas en esta etapa (Módulo 2)

| Servicio | Imagen | Puerto host | Propósito |
|---|---|---|---|
| `juice-shop` | `bkimminich/juice-shop:latest` | `3000` (`JUICE_SHOP_PORT`) | Aplicación web moderna (Node/Angular) con vulnerabilidades OWASP Top 10 deliberadas. Proyecto oficial de la OWASP Foundation. |
| `dvwa` | `vulnerables/web-dvwa:latest` | `3001` (`DVWA_PORT`) | Aplicación PHP/MySQL clásica de entrenamiento en vulnerabilidades web (SQLi, XSS, CSRF, etc.), con niveles de dificultad configurables. |

Ambas imágenes son proyectos de código abierto creados específicamente para
formación en seguridad ofensiva; ninguna contiene datos reales ni se conecta
a servicios externos para operar.

### Inicialización automática

- **Juice Shop** no requiere pasos de configuración: queda listo apenas el
  contenedor healthchequea OK.
- **DVWA** requiere que su base de datos MySQL se cree explícitamente
  (normalmente vía un botón en `setup.php`). El servicio `dvwa-init`
  (`lab/dvwa-init/`) automatiza exactamente esa misma petición HTTP tras el
  primer arranque, para no romper el requisito de "`docker compose up -d`
  sin pasos manuales". Ver [`lab/README.md`](../lab/README.md) para el
  detalle técnico.
- Credenciales por defecto de DVWA tras la inicialización: `admin` /
  `password` — válidas únicamente dentro de este laboratorio local.

## Ampliación futura

El mismo patrón (imagen contenida, en `lab-network`, con un `*-init` opcional
si la app lo requiere) permite sumar más adelante Metasploitable, WebGoat,
Mutillidae u otras aplicaciones vulnerables sin modificar la arquitectura ni
las reglas de aislamiento descritas aquí.

## Responsabilidad del usuario

Al desplegar este proyecto, el usuario acepta:

- Ejecutarlo únicamente contra los targets definidos en este laboratorio.
- No exponer los puertos publicados (`JUICE_SHOP_PORT`, `DVWA_PORT`, ni los
  del resto de la plataforma) a redes no confiables o a internet.
- Usar el proyecto con fines educativos, de investigación o de demostración
  de portfolio, nunca contra infraestructura de terceros.
