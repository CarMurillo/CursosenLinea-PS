from abc import ABC

from app.modules.courses.domain.models import Course


class CourseDecorator(Course, ABC):
    """
    Decorator base.

    Mantiene la misma interfaz de Course,
    pero permite agregar características.
    """

    def __init__(
        self,
        wrapped_course: Course
    ):

        self._wrapped_course = wrapped_course


    @property
    def course_id(self):
        return self._wrapped_course.course_id


    @course_id.setter
    def course_id(self, value):
        self._wrapped_course.course_id = value


    @property
    def title(self):
        return self._wrapped_course.title


    @title.setter
    def title(self, value):
        self._wrapped_course.title = value


    @property
    def instructor(self):
        return self._wrapped_course.instructor


    @instructor.setter
    def instructor(self, value):
        self._wrapped_course.instructor = value


    @property
    def price(self):
        return self._wrapped_course.price


    @price.setter
    def price(self, value):
        self._wrapped_course.price = value


    @property
    def enrolled_students(self):
        return self._wrapped_course.enrolled_students


    @enrolled_students.setter
    def enrolled_students(self, value):
        self._wrapped_course.enrolled_students = value


    @property
    def content(self):
        return self._wrapped_course.content


    @content.setter
    def content(self, value):
        self._wrapped_course.content = value


    def get_course_type(self) -> str:

        return self._wrapped_course.get_course_type()


    def get_details(self) -> dict:

        return self._wrapped_course.get_details()


class PremiumCourseDecorator(
    CourseDecorator
):
    """
    Agrega características Premium.
    """

    PREMIUM_SURCHARGE = 0.20


    @property
    def price(self):

        return round(
            self._wrapped_course.price
            * (1 + self.PREMIUM_SURCHARGE),
            2
        )


    def get_details(self):

        details = (
            self._wrapped_course
            .get_details()
            .copy()
        )

        decorators = list(
            details.get(
                "decorators",
                []
            )
        )

        decorators.append(
            "premium"
        )

        details["decorators"] = decorators

        details["premium"] = True

        details["premium_benefits"] = [
            "Contenido premium",
            "Acceso prioritario",
        ]

        details["base_price"] = (
            self._wrapped_course.price
        )

        details["price"] = self.price

        return details


class CertificateCourseDecorator(
    CourseDecorator
):
    """
    Agrega certificación al curso.
    """

    def get_details(self):

        details = (
            self._wrapped_course
            .get_details()
            .copy()
        )

        decorators = list(
            details.get(
                "decorators",
                []
            )
        )

        decorators.append(
            "certificate"
        )

        details["decorators"] = decorators

        details["certificate"] = True

        details[
            "certificate_description"
        ] = (
            "Certificado digital al "
            "completar el curso"
        )

        return details