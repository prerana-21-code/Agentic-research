"""
FastAPI Dependencies
Provides dependency injection providers for application services and pipeline singletons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from fastapi import HTTPException, Request, status

if TYPE_CHECKING:
    from backend.research_workflow import ResearchWorkflowService
    from rag_engine.integrated_pipeline import IntegratedRAGPipeline


def get_rag_pipeline(request: Request) -> IntegratedRAGPipeline:
    """
    Retrieves the singleton IntegratedRAGPipeline instance from application state.
    Guarantees that the embedding model and vector store are not re-initialized per request.
    """
    pipeline = getattr(request.app.state, "rag_pipeline", None)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Integrated RAG pipeline is not initialized.",
        )
    return pipeline


def get_research_workflow(request: Request) -> ResearchWorkflowService:
    """
    Retrieves the singleton ResearchWorkflowService instance from application state.
    """
    workflow = getattr(request.app.state, "research_workflow", None)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Research workflow service is not initialized.",
        )
    return workflow
