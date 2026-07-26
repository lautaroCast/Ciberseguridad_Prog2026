# Modelo de seguridad — Módulo 9

Este documento describe el modelo de autenticación elegido para VulnScan
Platform y, sobre todo, sus límites conocidos: qué protege, qué no
protege, y qué habría que cambiar si el alcance del proyecto creciera más
allá de un laboratorio local de un solo operador.

## Qué existe hoy

Dos niveles de secreto compartido, ninguno de los dos es un sistema de
usuarios:

- **`BACKEND_API_KEY`** — protege el Backend (todo excepto `/health`).
  Lo manda el Frontend (header `X-API-Key`) y n8n al llamar al Backend.
- **`INTERNAL_API_KEY`** — protege Scanner y Reports (todo excepto
  `/health`), que además dejaron de publicar su puerto al host. Lo mandan
  n8n (al llamar a Scanner) y el Backend (al llamar a Reports), header
  `X-Internal-Token`.

Ver `backend/app/security.py`, `scanner/app/security.py` y
`reports/app/security.py` para la implementación (misma forma en los
tres: `secrets.compare_digest` contra el valor esperado, 401 si no
matchea o falta el header).

## Limitaciones conocidas (a propósito, para revisar más adelante si hace falta)

- **La `BACKEND_API_KEY` queda visible en el bundle JS del Frontend.**
  Vite la inlinea en build time (`VITE_API_KEY`); cualquiera que abra el
  dashboard puede leerla con "ver código fuente" o las DevTools del
  navegador. No es un secreto real frente a un atacante con acceso al
  Frontend — solo evita el uso casual sin credenciales por parte de
  alguien que ni siquiera abrió el dashboard.
- **No hay noción de usuarios.** No se puede saber *quién* disparó un
  scan concreto o generó un reporte concreto, ni revocar acceso a una
  sola persona sin rotar la key para todos los que la usan (Frontend y
  n8n).
- **No hay rate limiting ni protección de fuerza bruta** sobre el header
  `X-API-Key` / `X-Internal-Token`. Un intento de fuerza bruta contra la
  key no queda ni detectado ni frenado a este nivel.
- **Rotar la key no es instantáneo.** Como `BACKEND_API_KEY` está
  inlineada en el bundle del Frontend en build time, rotarla implica
  reconfigurar `.env` **y rebuildear** el contenedor `frontend`, no solo
  cambiar una variable de entorno en caliente.
- **No hay TLS/HTTPS en ningún servicio.** Todo el tráfico interno
  (incluidas ambas keys) viaja en texto plano dentro de `app-network`.
  Razonable para un laboratorio que corre en `localhost`; no lo sería si
  esto se expusiera fuera de la máquina de desarrollo.
- **La descarga de reportes ya no es un link directo.** Como un `<a href>`
  no puede llevar headers custom, `GET /reports/{id}/download` pasó a
  requerir `X-API-Key` — el Frontend lo resuelve haciendo `fetch` con el
  header y convirtiendo la respuesta en un blob descargable
  (`frontend/src/api/client.ts::downloadFile`/`triggerDownload`). Es un
  detalle de implementación, no una debilidad, pero vale documentarlo
  porque cambia el patrón esperado si se agrega un nuevo endpoint de
  descarga en el futuro.

## Decisiones descartadas y por qué

- **Login real (usuario/contraseña) + JWT**: se evaluó explícitamente
  (ver historial del Módulo 9) y se descartó por alcance — hubiera
  requerido una tabla `users`, endpoints de login/logout, manejo de
  expiración de sesión, y una pantalla de login en el Frontend. Para un
  laboratorio de un solo operador, el costo no se justificaba frente al
  riesgo real que mitiga una API key compartida.
- **Credentials nativas de n8n** para los headers de los nodos HTTP en
  vez de `$env.*`: se descartó porque requeriría un paso manual de
  configuración en la UI de n8n antes de poder levantar el pipeline,
  rompiendo la premisa de "todo levanta con `docker compose up -d`, sin
  pasos manuales" que sostiene el resto del proyecto.

## Camino de mejora futura, si hace falta

Si en algún momento este proyecto necesita distinguir usuarios reales,
revocar acceso individual, o exponerse fuera de `localhost`:

1. Reemplazar la API key compartida por login (usuario/contraseña) + JWT
   de corta duración, con refresh token.
2. Agregar rate limiting a nivel de gateway/reverse proxy (ej. Nginx
   `limit_req`) delante del Backend.
3. Poner TLS delante de todos los servicios expuestos (al menos
   Frontend/Backend), vía un reverse proxy con certificados (Let's
   Encrypt en un deployment real, certificados self-signed para
   desarrollo).
4. Auditoría: registrar qué usuario disparó cada scan/reporte, no solo
   `triggered_by: "n8n-pipeline"` como hoy.
