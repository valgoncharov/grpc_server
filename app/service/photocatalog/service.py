import datetime
import uuid
import time
from typing import Iterator

import internal.pb.photocatalog_pb2_grpc as photocatalog_pb2_grpc
import internal.pb.photocatalog_pb2 as photocatalog_pb2
from grpc import ServicerContext, StatusCode
import google.protobuf.timestamp_pb2 as timestamp_pb2

from app.service.photocatalog.mock_repository import (
    PhotoResponseModel,
    TimeStampModel,
)
from app.service.photocatalog.protocol import Repository


class PhotoCatalogService(photocatalog_pb2_grpc.PhotoCatalogServiceServicer):
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    def Photo(
            self, request: photocatalog_pb2.IdRequest, context: ServicerContext
    ) -> photocatalog_pb2.PhotoResponse:
        photo = self._repository.get_photo(request.id)
        if not photo:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Photo with id {request.id} not found!")
            return photocatalog_pb2.PhotoResponse()

        response = photocatalog_pb2.PhotoResponse(
            id=photo.id,
            description=photo.description,
            timestamp=timestamp_pb2.Timestamp(
                seconds=photo.timestamp.seconds, nanos=photo.timestamp.nanos
            ),
            content=photo.content,
        )

        return response

    def AddPhoto(
            self, request: photocatalog_pb2.PhotoRequest, context: ServicerContext
    ) -> photocatalog_pb2.PhotoResponse:
        id_ = str(uuid.uuid4())
        photo_response = photocatalog_pb2.PhotoResponse(
            id=id_,
            description=request.description,
            content=request.content,
        )
        now = timestamp_pb2.Timestamp()
        now.FromDatetime(datetime.datetime.now())
        photo_response.timestamp.CopyFrom(now)

        photo_model = PhotoResponseModel(
            id=photo_response.id,
            description=photo_response.description,
            timestamp=TimeStampModel(
                seconds=photo_response.timestamp.seconds,
                nanos=photo_response.timestamp.nanos,
            ),
            content=photo_response.content,
        )
        self._repository.add_photo(photo_model)

        return photo_response

    def AddPhotos(
            self, request_iterator: Iterator[photocatalog_pb2.PhotoRequest], context: ServicerContext
    ) -> photocatalog_pb2.UploadStatusResponse:
        uploaded_ids = []

        for request in request_iterator:
            try:
                id_ = str(uuid.uuid4())
                photo_response = photocatalog_pb2.PhotoResponse(
                    id=id_,
                    description=request.description,
                    content=request.content,
                )
                now = timestamp_pb2.Timestamp()
                now.FromDatetime(datetime.datetime.now())
                photo_response.timestamp.CopyFrom(now)

                photo_model = PhotoResponseModel(
                    id=photo_response.id,
                    description=photo_response.description,
                    timestamp=TimeStampModel(
                        seconds=photo_response.timestamp.seconds,
                        nanos=photo_response.timestamp.nanos,
                    ),
                    content=photo_response.content,
                )
                self._repository.add_photo(photo_model)
                uploaded_ids.append(id_)
            except Exception as e:
                print(f"Error processing photo upload: {str(e)}")
                continue

        if uploaded_ids:
            return photocatalog_pb2.UploadStatusResponse(
                success=True,
                message=f"Successfully uploaded {len(uploaded_ids)} photos",
                uploaded_ids=uploaded_ids
            )
        else:
            return photocatalog_pb2.UploadStatusResponse(
                success=False,
                message="No photos were uploaded successfully",
                uploaded_ids=[]
            )

    def RandomPhotos(
            self, request: photocatalog_pb2.CountRequest, context: ServicerContext
    ) -> Iterator[photocatalog_pb2.PhotoResponse]:
        for photo in self._repository.get_random_photos(request.count):
            response = photocatalog_pb2.PhotoResponse(
                id=photo.id,
                description=photo.description,
                timestamp=timestamp_pb2.Timestamp(
                    seconds=photo.timestamp.seconds, nanos=photo.timestamp.nanos
                ),
                content=photo.content,
            )
            time.sleep(1)
            yield response