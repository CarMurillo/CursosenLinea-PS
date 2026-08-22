# CursosenLinea-PS

Carlos David Murillo Moreno
Juan David Villalobos Méndez

1. Introducción
El propósito de este proyecto es definir con claridad qué se va a construir, por qué, para quién y bajo qué restricciones técnicas, fases de diseño arquitectónico, modelado UML y desarrollo.
Se construirán los siguientes entregables: diagramas UML, ADRs (Architecture Decision Records), manuales técnicos y el propio repositorio del proyecto.

2. Definición del Proyecto
Plataforma de Cursos en Línea — LMS Avanzado
¿Qué es?
Un Sistema de Gestión de Aprendizaje (LMS — Learning Management System) de nueva generación, diseñado bajo una arquitectura de software (microservicios/hexagonal), que permite a instituciones educativas, instructores independientes o empresas de capacitación:
•	Crear, administrar y publicar cursos en línea.
•	Evaluar y certificar a los estudiantes.
•	Dictar clases en vivo mediante videoconferencia integrada.
•	Ofrecer una experiencia de aprendizaje personalizada mediante recomendaciones adaptativas.
•	Monetizar contenido a través de cursos premium con pasarela de pagos.
La diferencia de un LMS tradicional, este proyecto busca demostrar dominio de arquitectura de software profesional: separación de responsabilidades, bajo acoplamiento, alta cohesión, trazabilidad de decisiones de diseño, calidad de código verificable y operación observable en producción (logging/monitoreo).

4. Objetivos
   
Objetivo general
Diseñar y desarrollar una plataforma de gestión de cursos en línea aplicando una arquitectura basada en microservicios/hexagonal, patrones de diseño GoF, pruebas automatizadas, CI/CD, control de versiones y observabilidad del sistema.


Objetivos específicos
1.	Modelar el dominio del negocio (cursos, usuarios, evaluaciones, pagos, videoconferencias) mediante diagramas UML (casos de uso, clases, secuencia, componentes, despliegue).
2.	Diseñar una arquitectura hexagonal/de microservicios que desacople la lógica de negocio de la infraestructura (BD, frameworks, servicios externos).
3.	Implementar al menos 8 patrones de diseño GoF justificando su elección mediante ADRs.
4.	Garantizar la calidad y mantenibilidad del código mediante pruebas automatizadas con cobertura ≥ 80%.
5.	Implementar monitoreo y logging centralizado del sistema (ELK, Prometheus + Grafana o Datadog) para observar el comportamiento en tiempo de ejecución.

Justificación
Un LMS es un dominio ideal para un proyecto académico integrador porque:
•	Tiene múltiples subdominios naturales como gestión de cursos, evaluaciones, videoconferencia, pagos, recomendaciones, lo cual justifica de forma orgánica una arquitectura de microservicios en lugar de forzarla artificialmente.
•	Involucra reglas de negocio no triviales (progreso de un estudiante, condiciones de certificación, control de acceso a contenido premium) que se benefician de patrones de diseño reales, no decorativos.
•	Requiere integración con sistemas externos (pasarela de pagos, servicio de videoconferencia), lo cual es un buen caso de uso para el patrón hexagonal, separando el dominio de esas dependencias externas.
•	Es un producto con valor real y comprensible, útil como pieza de portafolio profesional más allá de la asignatura.
5. Alcance del Proyecto
 Dentro del alcance 
•	Gestión de cursos: creación, edición, publicación, módulos/lecciones.
•	Gestión de evaluaciones: quices, exámenes, calificación, emisión de certificados.
•	Videoconferencia integrada con grabación automática de sesiones (puede integrarse vía API de un proveedor externo, p. ej. Jitsi/Zoom/WebRTC, en lugar de construir el motor de video desde cero).
•	Motor de recomendación básico de aprendizaje adaptativo (reglas o modelo simple; no se espera un sistema de ML de producción).
•	Integración con pasarela de pagos para cursos premium (puede usarse un proveedor sandbox, p. ej. Stripe/PayU en modo pruebas).
•	Autenticación y autorización de usuarios (roles: estudiante, instructor, administrador).
•	Documentación arquitectónica completa (UML + ADRs).
•	Pipeline de CI/CD y monitoreo centralizado.
