# Bibliografía nueva (hallazgos C-16, C-17, A-17, A-18, A-19, A-21, A-22)

**Tramo:** 5 (bibliografía) — Prioridad 5 del auditor (§19), dentro de los tramos 1-8.

## Qué se retira

- **Hussain, A., Tahir, A., Hussain, Z., Jan, Z., Alam, M., & Javed, A. (2020).**
  *Automated security scanning for IoT networks using open-source tools.*
  IEEE Access, 8, 165996–166010. DOI 10.1109/ACCESS.2020.3022845 —
  referencia fabricada. El DOI existe y resuelve, pero a un artículo real
  y completamente distinto (Tran, Nguyen-Trong y Park, 2020, sobre
  antenas polarizadas circularmente). Ver `C-16.md`.
- **Sharma, A., & Bahl, S. (2021).** *Cybersecurity education through
  open-source laboratory environments: A pedagogical analysis.* Journal
  of Cybersecurity Education, Research and Practice, 2021(1), Art. 5 —
  no verificable, no aparece en el índice del volumen ni en bases
  bibliográficas. Ver `C-17.md`.

Retirar también las oraciones del §7 que se apoyan exclusivamente en
estas dos referencias, o reescribirlas para apoyarse en las nuevas.

## Qué se incorpora

10 artículos arbitrados reales, publicados 2021-2024, verificados en dos
pasos independientes: (1) búsqueda dirigida + resolución de DOI, (2)
verificación manual contra la API de Crossref (`api.crossref.org/works/
<DOI>`) confirmando que título, autores y revista coinciden exactamente
— no solo que el DOI "resuelve a algo". Los dos artículos fabricados
originales pasaban la prueba de "el DOI existe"; por eso el segundo paso
es obligatorio y no un formalismo.

### Para §7 (Estado del Arte)

1. **Bridges, R. A., Rice, A. E., Oesch, S., Nichols, J. A., Watson, C.,
   Spakes, K., Norem, S., Huettel, M., Jewell, B., Weber, B., Gannon, C.,
   Bizovi, O., Hollifield, S. C., & Erwin, S. (2023).** *Testing SOAR
   tools in use.* Computers & Security, 129, Article 103201.
   https://doi.org/10.1016/j.cose.2023.103201
   — Antecedente más directo del corpus: evaluación empírica de
   herramientas SOAR (Security Orchestration, Automation and Response)
   en uso real. Es el reemplazo natural de Hussain et al. como sostén de
   la afirmación sobre automatización de la respuesta/análisis de
   seguridad — con la ventaja de ser verificable y de tratar
   específicamente la orquestación, que es el aporte central de esta
   tesis (n8n cumple un rol análogo al de las plataformas SOAR que el
   artículo evalúa). Reutilizable también en §15 Discusión por sus
   hallazgos sobre limitaciones prácticas de SOAR.

2. **Bakhshi, T., Ghita, B., & Kuzminykh, I. (2024).** *A review of IoT
   firmware vulnerabilities and auditing techniques.* Sensors, 24(2),
   708. https://doi.org/10.3390/s24020708
   — Revisión reciente (2024) de técnicas de auditoría de
   vulnerabilidades; útil para posicionar la tesis dentro de la
   conversación activa del área con una fuente de los últimos dos años
   (la auditoría penalizó duramente que 0 referencias fueran de 2025-2026;
   esta y la #3 son 2024, el máximo disponible con relevancia directa).

3. **Bhandari, G. P., Assres, G., Gavric, N., Shalaginov, A., &
   Grønli, T.-M. (2024).** *IoTvulCode: AI-enabled vulnerability
   detection in software products designed for IoT applications.*
   International Journal of Information Security, 23(4).
   https://doi.org/10.1007/s10207-024-00848-6
   — Antecedente 2024 de detección automatizada de vulnerabilidades como
   línea de investigación activa.

4. **deRito, C., & Bhatia, S. (2022).** *Comparative analysis of
   open-source vulnerability scanners for IoT devices.* En D. J. Hemanth,
   D. Pelusi, & C. Vuppalapati (Eds.), *Intelligent Data Communication
   Technologies and Internet of Things* (Lecture Notes on Data
   Engineering and Communications Technologies, Vol. 101). Springer.
   https://doi.org/10.1007/978-981-16-7610-9_58
   — Antecedente directo sobre comparación y fragmentación de escáneres
   open-source: sostiene la premisa central de la introducción (§1-§3)
   sobre dispersión de herramientas y la necesidad de orquestarlas, con
   una fuente real en vez de la afirmación sin cita que había hasta ahora.

### Para §8 (Marco Teórico)

5. **Jacobs, J., Romanosky, S., Edwards, B., Roytman, M., &
   Adjerid, I. (2021).** *Exploit prediction scoring system (EPSS).*
   Digital Threats: Research and Practice, 2(3), Article 20.
   https://doi.org/10.1145/3436242
   — El propio §8.2 del informe de auditoría señala que el marco teórico
   describe CVSS sin discutir alternativas ni el debate vivo en la
   literatura (EPSS, catálogo KEV de CISA). Este artículo es la fuente
   primaria de EPSS — permite incorporar esa discusión con una cita real
   en vez de agregarla sin respaldo.

6. **Marandi, M., Bertia, A., & Silas, S. (2023).** *Implementing and
   automating security scanning to a DevSecOps CI/CD pipeline.* En 2023
   World Conference on Communication & Computing (WCONF). IEEE.
   https://doi.org/10.1109/WCONF58270.2023.10235015
   — Antecedente directo de orquestación automatizada de escaneo de
   seguridad en un pipeline, conceptualmente análogo a la orquestación
   vía n8n de la plataforma.

7. **Rahman, A., Shamim, S. I., Bose, D. B., & Pandita, R. (2023).**
   *Security misconfigurations in open source Kubernetes manifests: An
   empirical study.* ACM Transactions on Software Engineering and
   Methodology, 32(4), Article 99. https://doi.org/10.1145/3579639
   — Estudio empírico sobre errores de configuración de seguridad en
   arquitecturas orquestadas por contenedores; relevante para justificar
   decisiones de diseño de la plataforma (Docker, servicios separados) y
   para el propio §13 (análisis de riesgos de la arquitectura).

8. **Nasab, A. R., Shahin, M., Hoseyni Raviz, S. A., Liang, P.,
   Mashmool, A., & Lenarduzzi, V. (2023).** *An empirical study of
   security practices for microservices systems.* Journal of Systems and
   Software, 198, Article 111563. https://doi.org/10.1016/j.jss.2022.111563
   — Antecedente empírico sobre prácticas de seguridad en arquitecturas
   de microservicios, aplicable a la justificación arquitectónica de la
   plataforma (Scanner Service, Backend, Reports como servicios
   independientes).

### Para §9 (Metodología — justificación del laboratorio controlado)

9. **Księżopolski, B., Mazur, K., Miśkiewicz, M., & Rusinek, D. (2022).**
   *Teaching a hands-on CTF-based web application security course.*
   Electronics, 11(21), 3517. https://doi.org/10.3390/electronics11213517
   — Antecedente académico real sobre el uso pedagógico de entornos
   vulnerables controlados (mismo espíritu que Juice Shop/DVWA), para
   justificar metodológicamente la elección del laboratorio como banco de
   pruebas.

10. **Su, J.-M. (2024).** *WebHOLE: Developing a web-based hands-on
    learning environment to assist beginners in learning web application
    security.* Education and Information Technologies, 29(6).
    https://doi.org/10.1007/s10639-023-12090-z
    — Complementa a la referencia anterior con un enfoque más reciente y
    específico en principiantes; cubre el mismo hueco metodológico con
    una segunda fuente independiente.

## Candidatos evaluados y descartados (para que quede el rastro de qué se intentó)

- *Explainable Risk-Based Vulnerability Prioritization... (CVSS+EPSS+KEV)*,
  World Journal of Advanced Research and Reviews — temáticamente ideal,
  pero la revista (GSC Online Press) no tiene indexación confiable en
  Scopus/WoS confirmable. Descartada por riesgo de credibilidad ante
  tribunal.
- Melara & Bowman, *Enabling Security-Oriented Orchestration of
  Microservices* — solo existe como preprint arXiv (2106.09841), sin
  publicación arbitrada confirmada.
- Lee, Jang-Jaccard & Kwak (2022), *Novel Architecture of SOAR in
  Internet of Blended Environment*, Computers, Materials & Continua
  (DOI 10.32604/cmc.2022.028495) — el DOI resuelve y coincide, pero la
  revista fue removida del Web of Science en 2023 por problemas de
  control de calidad editorial. Descartada por ese riesgo pese a ser
  técnicamente verificable.
- Johnson, Jones, Chavez & Hossain-McKenzie (2023), *SOAR4DER* (Springer,
  DOI 10.1007/978-3-031-20360-2_16) — real y verificado, pero su foco
  (recursos energéticos distribuidos/SCADA) es demasiado tangencial al
  escaneo web/red de esta tesis. Queda como backup si hiciera falta un
  onceavo artículo sobre SOAR.
- Un artículo sobre benchmarking de herramientas DAST (atribuido a
  "Journal of Engineering and Applied Sciences Technology", 2024) y un
  paper sobre automatización de seguridad con n8n self-hosted (hallado en
  Semantic Scholar) — ninguno de los dos pudo confirmarse con metadatos
  limpios en Crossref. Descartados, no verificables.

## Verificación

Cada una de las 10 referencias fue confirmada de forma independiente
contra `https://api.crossref.org/works/<DOI>` — título, autores y
revista/serie coinciden exactamente con lo citado arriba. Antes de
entregar la tesis, re-verificar una vez más si pasa suficiente tiempo
(las bases bibliográficas pueden actualizar metadatos).
