"""
Módulo: Courses - Capa de Dominio (Domain)
Patrón de Diseño: Prototype (Creacional)
"""

import copy
import uuid


class PrototypeCourse:
    """
    Implementación del Patrón Prototype sobre la entidad Course.
    """

    def __init__(self, title: str, description: str, instructor_id: str, price: float, modules: list):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.instructor_id = instructor_id
        self.price = price
        self.modules = modules

    def clone(self, new_title: str = None, new_instructor_id: str = None) -> 'PrototypeCourse':
        """
        Realiza una copia profunda (Deep Copy) garantizando que objetos anidados
        (módulos y lecciones) tengan sus propios IDs únicos y nuevos en memoria.
        """
        cloned_course = copy.deepcopy(self)
        cloned_course.id = str(uuid.uuid4())
        
        # Regenerar UUIDs únicos para la jerarquía clonada
        for module in cloned_course.modules:
            if hasattr(module, 'id'):
                module.id = str(uuid.uuid4())
            if hasattr(module, 'lessons'):
                for lesson in module.lessons:
                    if hasattr(lesson, 'id'):
                        lesson.id = str(uuid.uuid4())

        if new_title:
            cloned_course.title = new_title
        else:
            cloned_course.title = f"{self.title} (Copia)"

        if new_instructor_id:
            cloned_course.instructor_id = new_instructor_id

        return cloned_course