import sys
from pathlib import Path

# Agregar la carpeta 'lms_backend' al PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Importaciones de los patrones
from app.modules.courses.domain.builder import CourseBuilder
from app.modules.courses.domain.prototype import PrototypeCourse

# 1. Probar Builder
builder = CourseBuilder(title="Patrones de Software en Python", instructor_id="inst_123")
course_built = (
    builder.set_description("Aprende Clean Architecture y SOLID")
    .set_price(49.99)
    .set_category("Programación")
    .add_tag("Python")
    .add_module("Módulo 1: Patrones Creacionales", [
        {"title": "Builder & Prototype", "content": "Explicación teórica", "duration_minutes": 30}
    ])
    .build()
)

print(f"✅ Curso Creado con Builder: {course_built.title} (ID: {course_built.id})")
print(f"   Módulos: {len(course_built.modules)}, Precio: ${course_built.price}")

# 2. Probar Prototype
prototype_item = PrototypeCourse(
    title=course_built.title,
    description=course_built.description,
    instructor_id=course_built.instructor_id,
    price=course_built.price,
    modules=course_built.modules
)

cloned_course = prototype_item.clone(new_title="Patrones de Software - Semestre 2026-2")

print(f"✅ Curso Clonado con Prototype: {cloned_course.title} (ID: {cloned_course.id})")
print(f"   ¿IDs de curso son distintos?: {course_built.id != cloned_course.id}")