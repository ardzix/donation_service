import hashlib
import io
from base64 import b64decode

from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.conf import settings

from libs.storage import STORAGE_CHUNK
from ..models import File, ChunkedUpload

from ..serializers.chunk_upload import ChunkUploadSerializer

MAX_FILE_SIZE = getattr(settings, "UPLOAD_MAX_FILE_SIZE", None)


class ChunkUploadViewSet(GenericViewSet):
    serializer_class = ChunkUploadSerializer
    permission_classes = (IsAuthenticated,)
    file_model_class = File

    def create(self, request):
        """
        Chunk upload file.

        ### Requires
        * __file_name__
        * __chunk__
        * __chunk_no__
        * __checksum__
        * __chunk_count__
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        storage = STORAGE_CHUNK
        chunk = serializer.validated_data.get("chunk")
        file_name = serializer.validated_data.get("file_name")
        chunk_no = serializer.validated_data.get("chunk_no")
        checksum = serializer.validated_data.get("checksum")
        chunk_count = serializer.validated_data.get("chunk_count")

        if request.GET.get("is_init"):
            _data, created = ChunkedUpload.objects.get_or_create(
                created_by=request.user,
                filename=file_name,
            )
            data_response = {"created": created}

        elif request.GET.get("is_checksum"):
            base64_str = ""
            for iterate in range(chunk_count):
                chunk_file_name = file_name + ".part_" + str(iterate)
                chunk_file = storage.open(chunk_file_name, mode="r")
                base64_str += str(chunk_file.read())
                storage.delete(chunk_file_name)

            base64_bytes = base64_str.encode("utf-8")
            hash_md5 = hashlib.md5()
            hash_md5.update(base64_bytes)

            if checksum == hash_md5.hexdigest():
                file = b64decode(base64_str.split(",")[-1])

                with io.BytesIO() as f:
                    f.write(file)
                    storage.save(file_name, f)

                chunk_file = storage.open(file_name)
                file_size = chunk_file.size
                # check size
                print(file_size, MAX_FILE_SIZE)
                if MAX_FILE_SIZE and file_size > MAX_FILE_SIZE:
                    storage.delete(file_name)
                    return Response(
                        {
                            "message": "Failed upload file",
                            "data": {
                                "file_size": file_size,
                                "allowed_size": MAX_FILE_SIZE,
                            },
                        }
                    )

                # save to file
                file_instance = self.file_model_class.objects.create(
                    created_by=request.user, name=file_name
                )
                file_instance.file.save(file_name, chunk_file, save=True)

                # delete chunk file
                storage.delete(file_name)

                return Response(
                    {
                        "message": "Success upload file",
                        "data": {
                            "url": file_instance.get_file(),
                            "file_id32": file_instance.id32,
                            "file_name": file_instance.name,
                        },
                    }
                )

        else:
            with io.StringIO() as f:
                f.write(chunk)
                storage.save(file_name + ".part_" + str(chunk_no), f)

            data_response = {
                "chunk_no": chunk_no,
            }

        return Response(data_response)
