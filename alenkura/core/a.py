from core.models import Estudiante
from accounts.models import User

def estudiantes_global(request):
    student = Estudiante.objects.all()
    users = User.objects.filter(role="TEACHER")
    return {
        'estudiantes': student,
        'users': users
    }