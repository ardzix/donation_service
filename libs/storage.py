"""
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# File: storage.py
# Project: core.ayopeduli.id
# File Created: Wednesday, 31st October 2018 7:26:00 pm
#
# Author: Arif Dzikrullah
#         ardzix@hotmail.com>
#         https://github.com/ardzix/>
#
# Last Modified: Wednesday, 31st October 2018 7:26:01 pm
# Modified By: arifdzikrullah (ardzix@hotmail.com>)
#
# Peduli sesama, sejahtera bersama
# Copyright - 2018 Ayopeduli.Id, ayopeduli.id
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""


from django.conf import settings
from django.core.files.storage import FileSystemStorage, DefaultStorage
from storages.backends.s3boto3 import S3Boto3Storage


USE_S3 = getattr(settings, "USE_S3", False)
USE_DO_SPACE = getattr(settings, "USE_DO_SPACE", False)  # use S3 credentials
USE_GCS = getattr(settings, "USE_GCS", False)
USE_RACKSPACE = getattr(settings, "USE_RACKSPACE", False)
GCS_BASE_URL = getattr(settings, "GCS_BASE_URL", "")
RACKSPACE_BASE_URL = getattr(settings, "RACKSPACE_BASE_URL", "")
BUCKET_LOCATION = getattr(settings, "BUCKET_LOCATION", "file")

# for DO bucket location
USE_DEFAULT_LOCATION = getattr(settings, "USE_DEFAULT_LOCATION", False)
DO_SPACE_LOCATION = getattr(settings, "DO_SPACE_LOCATION", False)

CHUNK_UPLOAD_ROOT = getattr(
    settings, "CHUNK_UPLOAD_FOLDER", "/srv/media/chunked/upload/"
)
CHUNK_UPLOAD_FINISHED_ROOT = getattr(
    settings, "CHUNK_UPLOAD_FOLDER", "/srv/media/chunked/final/"
)


def get_bucket_location(storage_type):
    if USE_DEFAULT_LOCATION and DO_SPACE_LOCATION:
        return ROOT_URL + storage_type

    return ROOT_URL


if settings.PRODUCTION:
    ROOT_URL = ""
    MEDIA_ROOT = settings.MEDIA_ROOT
    UPLOAD_ROOT = "%supload/" % settings.BASE_URL
else:
    ROOT_URL = "dev/"
    MEDIA_ROOT = settings.MEDIA_ROOT
    UPLOAD_ROOT = "%sstatic/upload/" % settings.BASE_URL

if USE_DO_SPACE and DO_SPACE_LOCATION:
    ROOT_URL = DO_SPACE_LOCATION

if USE_S3 or USE_DO_SPACE:
    FILE_STORAGE = S3Boto3Storage(
        location=get_bucket_location(BUCKET_LOCATION), file_overwrite=False
    )
else:
    FILE_STORAGE = FileSystemStorage(
        location=f"{MEDIA_ROOT}/{BUCKET_LOCATION}", base_url=f"{UPLOAD_ROOT}{BUCKET_LOCATION}"
    )


# chunk upload storage
STORAGE_CHUNK = FileSystemStorage(
    location=settings.MEDIA_ROOT + "/chunk",
    base_url="%sstatic/upload/chunk/" % settings.BASE_URL,
)

CHUNK_UPLOAD_PRIVATE = FileSystemStorage(location=CHUNK_UPLOAD_FINISHED_ROOT)
