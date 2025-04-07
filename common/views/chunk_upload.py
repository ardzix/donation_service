import hashlib
import io
from base64 import b64decode

from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.conf import settings

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from libs.storage import STORAGE_CHUNK
from ..models import File, ChunkedUpload
from ..serializers.chunk_upload import ChunkUploadSerializer

MAX_FILE_SIZE = getattr(settings, "UPLOAD_MAX_FILE_SIZE", None)


class ChunkUploadViewSet(GenericViewSet):
    """
    A viewset for handling chunked file uploads.

    Workflow:
    1. `?is_init=true` – initialize the upload and create a session.
    2. Upload chunks (`POST` with chunk data).
    3. `?is_checksum=true` – finalize upload by verifying all chunks and saving the full file.
    """
    serializer_class = ChunkUploadSerializer
    permission_classes = (IsAuthenticated,)
    file_model_class = File

    @swagger_auto_schema(
        operation_description="""
        Handle chunked file upload lifecycle:

        1. **Initialize Upload** (`?is_init=true`)  
           - Required fields: `file_name`
           - Response: whether session was created

        2. **Upload Chunk** (default POST)
           - Required fields:
             - `file_name`
             - `chunk`
             - `chunk_no`
             - `chunk_count`

        3. **Finalize Upload** (`?is_checksum=true`)
           - Required fields:
             - `file_name`
             - `chunk_count`
             - `checksum` (full base64 MD5 hash)
           - Verifies and saves the final file
        """,
        request_body=ChunkUploadSerializer,
        manual_parameters=[
            openapi.Parameter('is_init', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, required=False,
                              description="Initialize upload session"),
            openapi.Parameter('is_checksum', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, required=False,
                              description="Finalize upload by verifying checksum")
        ],
        responses={
            200: openapi.Response(
                description="Successful upload response or chunk status",
                examples={
                    "application/json": {
                        "message": "Success upload file",
                        "data": {
                            "url": "https://cdn.yourapp.com/files/image.png",
                            "file_id32": "abc123",
                            "file_name": "image.png"
                        }
                    }
                }
            )
        }
    )
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        storage = STORAGE_CHUNK
        chunk = serializer.validated_data.get("chunk")
        file_name = serializer.validated_data.get("file_name")
        chunk_no = serializer.validated_data.get("chunk_no")
        checksum = serializer.validated_data.get("checksum")
        chunk_count = serializer.validated_data.get("chunk_count")

        # INIT: create or reuse chunk upload session
        if request.GET.get("is_init"):
            _data, created = ChunkedUpload.objects.get_or_create(
                filename=file_name,
            )
            return Response({"created": created})

        # FINALIZE: verify checksum, merge and save
        elif request.GET.get("is_checksum"):
            base64_str = ""
            for i in range(chunk_count):
                chunk_file_name = file_name + f".part_{i}"
                chunk_file = storage.open(chunk_file_name, mode="r")
                base64_str += str(chunk_file.read())
                storage.delete(chunk_file_name)

            base64_bytes = base64_str.encode("utf-8")
            hash_md5 = hashlib.md5()
            hash_md5.update(base64_bytes)

            if checksum == hash_md5.hexdigest():
                file_data = b64decode(base64_str.split(",")[-1])
                with io.BytesIO() as f:
                    f.write(file_data)
                    storage.save(file_name, f)

                chunk_file = storage.open(file_name)
                file_size = chunk_file.size

                if MAX_FILE_SIZE and file_size > MAX_FILE_SIZE:
                    storage.delete(file_name)
                    return Response({
                        "message": "Failed upload file",
                        "data": {
                            "file_size": file_size,
                            "allowed_size": MAX_FILE_SIZE,
                        },
                    })

                file_instance = self.file_model_class.objects.create(
                    name=file_name
                )
                file_instance.file.save(file_name, chunk_file, save=True)
                storage.delete(file_name)

                return Response({
                    "message": "Success upload file",
                    "data": {
                        "url": file_instance.get_file(),
                        "file_id": file_instance.pk,
                        "file_name": file_instance.name,
                    },
                })

        # CHUNK UPLOAD: write part file
        with io.StringIO() as f:
            f.write(chunk)
            storage.save(file_name + f".part_{chunk_no}", f)

        return Response({
            "chunk_no": chunk_no,
        })
