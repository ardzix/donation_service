import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework import serializers
from ..models import File

def serialize_fields(instance, representation, field_serializer_map):
    """
    Serialize one or more fields of a serializer instance and insert into the representation.
    
    Parameters:
    - instance: the model instance being serialized
    - representation: the dictionary being returned by to_representation
    - field_serializer_map: a dict of field_name: (serializer_class, many_bool)
    """
    for field_name, (serializer_class, many) in field_serializer_map.items():
        field_value = getattr(instance, field_name, None)

        if field_value is None:
            continue

        if many:
            # Handles ManyToMany or reverse FK (related managers with `.all()`)
            if hasattr(field_value, 'all'):
                serialized = serializer_class(field_value.all(), many=True).data
            elif isinstance(field_value, (list, tuple)):
                serialized = serializer_class(field_value, many=True).data
            else:
                continue  # not a valid many field
        else:
            serialized = serializer_class(field_value).data

        representation[field_name] = serialized

class FileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ("id", "name", "file", "url", "file_size", "description")

    def get_url(self, instance):
        return instance.file.url if instance.file else "-"

    def get_file_size(self, instance):
        if instance.file and instance.file.size:
            return instance.file.size  # Size in bytes
        return None


class FileLiteSerializer(FileSerializer):

    class Meta:
        model = File
        fields = ("id", "name", "url", "file_size")


def decode_base64_img(encoded_file, name="temp"):
    file_format, imgstr = encoded_file.split(";base64,")
    ext = file_format.split("/")[-1]

    # Add padding if required
    missing_padding = len(imgstr) % 4
    if missing_padding:
        imgstr += "=" * (4 - missing_padding)

    data = ContentFile(base64.b64decode(imgstr), name=name + "." + ext)
    return data


class FileCreateSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    file_base64 = serializers.CharField(
        write_only=True, help_text="Base64 encoded file data"
    )
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ("id", "name", "url", "file_size",
                  "file_base64", "description")
        read_only_fields = ["id"]

    def get_url(self, instance):
        return instance.file.url if instance.file else "-"

    def get_file_size(self, instance):
        if instance.file and instance.file.size:
            return instance.file.size  # Size in bytes
        return None

    def validate(self, data):
        encoded_file = data.pop("file_base64")
        data["file"] = decode_base64_img(encoded_file, name=data["name"])
        return data


class SetFileSerializer(serializers.Serializer):
    file_base64 = serializers.CharField(
        write_only=True, help_text="Base64 encoded file data"
    )

    def create(self, validated_data):
        user = self.context.get("request").user
        encoded_file = validated_data["file_base64"]
        data = decode_base64_img(encoded_file)

        # Create File instance
        file_instance = File.objects.create(
            name=data.name, file=data, created_by=user)
        return file_instance
