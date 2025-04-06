from rest_framework import serializers


class ChunkUploadSerializer(serializers.Serializer):
    file_name = serializers.CharField()
    chunk = serializers.CharField(required=False)
    chunk_no = serializers.IntegerField(required=False)
    checksum = serializers.CharField(required=False)
    chunk_count = serializers.IntegerField(required=False)
