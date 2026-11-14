from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, Request

from backend.app.schemas.project import (
    AnnotationList,
    AnnotationResponse,
    PointCloudResponse,
    ProjectDetail,
    ProjectList,
    ProjectSummary,
)
from backend.app.services.project_service import (
    DatasetNotFoundError,
    ProjectNotFoundError,
    ProjectService,
)


router = APIRouter(prefix="/projects", tags=["projects"])
SLUG = Path(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=1, max_length=64)


def service(request: Request) -> ProjectService:
    return request.app.state.project_service


@router.get("", response_model=ProjectList)
def list_projects(request: Request) -> ProjectList:
    return ProjectList(
        items=[ProjectSummary(**project.__dict__) for project in service(request).list_published()]
    )


@router.get("/{slug}", response_model=ProjectDetail)
def get_project(request: Request, slug: str = SLUG) -> ProjectDetail:
    try:
        project = service(request).get_published(slug)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error
    return ProjectDetail(**project.__dict__)


@router.get("/{slug}/point-cloud", response_model=PointCloudResponse)
def get_point_cloud(request: Request, slug: str = SLUG) -> PointCloudResponse:
    try:
        dataset = service(request).get_primary_dataset(slug)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error
    except DatasetNotFoundError as error:
        raise HTTPException(status_code=404, detail="Point cloud not found") from error
    return PointCloudResponse(
        name=dataset.name,
        ept_url=f"/pointclouds/{slug}/{dataset.ept_path}",
        epsg=dataset.epsg,
        point_count=dataset.point_count,
        size_bytes=dataset.size_bytes,
        bounds=dataset.bounds,
    )


@router.get("/{slug}/annotations", response_model=AnnotationList)
def list_annotations(request: Request, slug: str = SLUG) -> AnnotationList:
    try:
        annotations = service(request).list_annotations(slug)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error
    return AnnotationList(
        items=[AnnotationResponse(**annotation.__dict__) for annotation in annotations]
    )
