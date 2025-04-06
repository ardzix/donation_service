from rest_framework import viewsets, permissions
from ..models import File
from ..serializers import FileCreateSerializer

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post"]

