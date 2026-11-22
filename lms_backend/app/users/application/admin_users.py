"""Casos de uso de administración de usuarios (solo admin).

- `UserDetailService`: ficha completa de un usuario. Para estudiantes reúne
  cursos inscritos con su estado (sin iniciar / iniciado / terminado, a partir
  del % de avance que calcula el ProgressVisitor), certificados y pagos. Para
  instructores, los cursos que dicta y sus estudiantes.
- `DeleteUserUseCase`: elimina estudiantes e instructores. Un instructor con
  cursos no se elimina (sus cursos quedarían sin dueño): hay que suspenderlo.
  Al estudiante se le quita de las inscripciones; pagos y certificados se
  conservan como historial (auditoría y verificación pública).
- `SetUserStatusUseCase`: suspende o reactiva estudiantes e instructores. La
  suspensión es inmediata: `get_current_user` rechaza (401) cualquier token de
  un usuario inactivo y el login también lo rechaza.

Depende de puertos (repositorios y lector de progreso), no de FastAPI.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from app.modules.auth.domain.models import Role
from app.modules.certificates.domain.ports import CertificateRepository
from app.modules.courses.domain.ports import CourseRepository
from app.modules.payments.domain.ports import PaymentRepository
from app.users.domain.repositories import UserRecord, UserRepository

# (user_id, course_id) -> porcentaje de avance 0-100.
ProgressPercent = Callable[[str, str], float]

STATUS_NOT_STARTED = "sin_iniciar"
STATUS_IN_PROGRESS = "iniciado"
STATUS_COMPLETED = "terminado"

MANAGEABLE_ROLES = {Role.STUDENT.value, Role.INSTRUCTOR.value}


class UserNotFoundError(LookupError):
    pass


class UserStatusNotAllowedError(ValueError):
    """Solo se suspenden estudiantes e instructores (no admins ni a uno mismo)."""


class UserHasCoursesError(Exception):
    """El instructor tiene cursos: no se elimina (HTTP 409)."""


def course_status(percentage: float) -> str:
    if percentage >= 100:
        return STATUS_COMPLETED
    if percentage > 0:
        return STATUS_IN_PROGRESS
    return STATUS_NOT_STARTED


def user_summary(user: UserRecord) -> dict:
    created = getattr(user, "created_at", None)
    return {
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "role": user.role,
        "is_active": bool(user.is_active),
        "created_at": created.isoformat() if created else None,
    }


class UserDetailService:
    def __init__(
        self,
        users: UserRepository,
        courses: CourseRepository,
        progress_percent: ProgressPercent,
        certificates: CertificateRepository,
        payments: PaymentRepository,
    ):
        self._users = users
        self._courses = courses
        self._progress = progress_percent
        self._certificates = certificates
        self._payments = payments

    def get(self, user_id: str) -> dict:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        detail = user_summary(user)
        if user.role == Role.STUDENT.value:
            detail["student"] = self._student_detail(user.id)
        elif user.role == Role.INSTRUCTOR.value:
            detail["instructor"] = self._instructor_detail(user.id)
        return detail

    def _student_detail(self, user_id: str) -> dict:
        certificates = [c.to_dict() for c in self._certificates.list_by_user(user_id)]
        certified = {c["course_id"] for c in certificates}
        courses: List[dict] = []
        for course in self._courses.list_all():
            if user_id not in course.enrolled_students:
                continue
            pct = round(float(self._progress(user_id, course.course_id)), 2)
            courses.append({
                "course_id": course.course_id,
                "title": course.title,
                "instructor": course.instructor,
                "progress": pct,
                "status": course_status(pct),
                "has_certificate": course.course_id in certified,
            })
        courses.sort(key=lambda c: c["title"])
        counts = {s: 0 for s in (STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_COMPLETED)}
        for c in courses:
            counts[c["status"]] += 1
        return {
            "enrolled_count": len(courses),
            "not_started_count": counts[STATUS_NOT_STARTED],
            "in_progress_count": counts[STATUS_IN_PROGRESS],
            "completed_count": counts[STATUS_COMPLETED],
            "certificate_count": len(certificates),
            "courses": courses,
            "certificates": certificates,
            "payments": [p.to_dict() for p in self._payments.list_by_user(user_id)],
        }

    def _instructor_detail(self, user_id: str) -> dict:
        courses = []
        for course in self._courses.list_all():
            if course.instructor_id != user_id:
                continue
            details = course.get_details()
            courses.append({
                "course_id": course.course_id,
                "title": course.title,
                "price": course.price,
                "type": details.get("type"),
                "premium": bool(details.get("premium")),
                "certificate": bool(details.get("certificate")),
                "student_count": len(course.enrolled_students),
            })
        courses.sort(key=lambda c: c["title"])
        return {
            "course_count": len(courses),
            "student_count": sum(c["student_count"] for c in courses),
            "courses": courses,
        }


class SetUserStatusUseCase:
    def __init__(self, users: UserRepository):
        self._users = users

    def execute(self, user_id: str, *, is_active: bool, acting_admin_id: Optional[str]) -> dict:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        _ensure_manageable(user, acting_admin_id, "suspender o reactivar")
        updated = self._users.set_active(user_id, is_active)
        return user_summary(updated)


def _ensure_manageable(user: UserRecord, acting_admin_id: Optional[str], verb: str) -> None:
    if user.id == acting_admin_id:
        raise UserStatusNotAllowedError(f"No puedes {verb} tu propia cuenta.")
    if user.role not in MANAGEABLE_ROLES:
        raise UserStatusNotAllowedError(
            f"Solo se pueden {verb} estudiantes e instructores.")


class DeleteUserUseCase:
    def __init__(self, users: UserRepository, courses: CourseRepository):
        self._users = users
        self._courses = courses

    def execute(self, user_id: str, *, acting_admin_id: Optional[str]) -> dict:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        _ensure_manageable(user, acting_admin_id, "eliminar")

        owned = [c.title for c in self._courses.list_all() if c.instructor_id == user_id]
        if owned:
            raise UserHasCoursesError(
                f"El instructor tiene {len(owned)} curso(s) ({', '.join(owned)}). "
                "Suspéndelo en lugar de eliminarlo.")

        removed_from = []
        for course in self._courses.list_all():
            if user_id in course.enrolled_students:
                course.enrolled_students.remove(user_id)
                self._courses.save(course)
                removed_from.append(course.course_id)

        summary = user_summary(user)
        self._users.delete(user_id)
        return {"deleted": summary, "removed_enrollments": len(removed_from)}
