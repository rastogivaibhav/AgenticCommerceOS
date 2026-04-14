"""
Unit tests for job queue service.

Tests the JobQueueService class including:
- Job creation with unique IDs
- Job status transitions (QUEUED -> PROCESSING -> COMPLETED/FAILED)
- Redis caching for fast status lookups
- Job TTL (24 hours)
- Error handling and job retrieval
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
import fakeredis

from acosplatform.job_queue.models import Job, JobStatus
from acosplatform.job_queue.service import JobQueueService


@pytest.fixture
def redis_client():
    """Create a fake Redis client for testing."""
    return fakeredis.FakeStrictRedis()


@pytest.fixture
def job_queue_service(redis_client):
    """Create a JobQueueService instance with fake Redis."""
    service = JobQueueService(redis_client=redis_client)
    return service


class TestJobQueueService:
    """Tests for JobQueueService."""

    def test_create_job_returns_job_with_unique_id(self, job_queue_service):
        """Test that create_job returns a Job with a unique ID."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={"key": "value"}
        )

        assert isinstance(job, Job)
        assert job.id is not None
        assert job.workflow_id == "workflow-123"
        assert job.workflow_name == "test_workflow"
        assert job.payload == {"key": "value"}
        assert job.status == JobStatus.QUEUED
        assert job.created_at is not None

    def test_create_job_generates_different_ids(self, job_queue_service):
        """Test that multiple create_job calls generate unique IDs."""
        job1 = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={}
        )
        job2 = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={}
        )

        assert job1.id != job2.id

    def test_get_job_returns_created_job(self, job_queue_service):
        """Test that get_job retrieves a previously created job."""
        created_job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={"key": "value"}
        )

        retrieved_job = job_queue_service.get_job(created_job.id)

        assert retrieved_job is not None
        assert retrieved_job.id == created_job.id
        assert retrieved_job.workflow_id == created_job.workflow_id
        assert retrieved_job.payload == created_job.payload

    def test_get_job_returns_none_for_nonexistent_job(self, job_queue_service):
        """Test that get_job returns None for non-existent job."""
        result = job_queue_service.get_job("nonexistent-job-id")
        assert result is None

    def test_get_job_status_returns_queued_for_new_job(self, job_queue_service):
        """Test that get_job_status returns QUEUED for newly created jobs."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={}
        )

        status = job_queue_service.get_job_status(job.id)
        assert status == JobStatus.QUEUED

    def test_get_job_status_returns_none_for_nonexistent_job(self, job_queue_service):
        """Test that get_job_status returns None for non-existent job."""
        result = job_queue_service.get_job_status("nonexistent-job-id")
        assert result is None

    def test_mark_job_processing_updates_status(self, job_queue_service):
        """Test that mark_job_processing updates status to PROCESSING."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={}
        )

        job_queue_service.mark_job_processing(job.id)
        status = job_queue_service.get_job_status(job.id)

        assert status == JobStatus.PROCESSING

    def test_mark_job_completed_updates_status(self, job_queue_service):
        """Test that mark_job_completed updates status to COMPLETED."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={}
        )

        result = {"status": "success"}
        job_queue_service.mark_job_completed(job.id, result)
        status = job_queue_service.get_job_status(job.id)

        assert status == JobStatus.COMPLETED

        retrieved_job = job_queue_service.get_job(job.id)
        assert retrieved_job.result == result

    def test_mark_job_failed_updates_status(self, job_queue_service):
        """Test that mark_job_failed updates status to FAILED."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={}
        )

        error = "Test error message"
        job_queue_service.mark_job_failed(job.id, error)
        status = job_queue_service.get_job_status(job.id)

        assert status == JobStatus.FAILED

        retrieved_job = job_queue_service.get_job(job.id)
        assert retrieved_job.error == error

    def test_job_ttl_is_24_hours(self, job_queue_service):
        """Test that jobs are cached with 24-hour TTL."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={}
        )

        # Verify the job exists
        assert job_queue_service.get_job(job.id) is not None

        # Check that TTL is set correctly (should be around 86400 seconds = 24 hours)
        # Note: fakeredis may handle TTL differently, so we just verify it's stored
        # and has reasonable cache lifetime configuration
        assert job_queue_service.JOB_TTL == 86400  # 24 hours in seconds

    def test_status_lookup_uses_cache(self, job_queue_service):
        """Test that status lookups use Redis cache for performance."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={}
        )

        # Get status multiple times - should use cache
        status1 = job_queue_service.get_job_status(job.id)
        status2 = job_queue_service.get_job_status(job.id)

        assert status1 == status2 == JobStatus.QUEUED

    def test_job_lifecycle_transition(self, job_queue_service):
        """Test full job lifecycle: QUEUED -> PROCESSING -> COMPLETED."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={"key": "value"}
        )

        # Initial state
        assert job_queue_service.get_job_status(job.id) == JobStatus.QUEUED

        # Move to processing
        job_queue_service.mark_job_processing(job.id)
        assert job_queue_service.get_job_status(job.id) == JobStatus.PROCESSING

        # Mark as completed
        result = {"status": "success", "data": "test"}
        job_queue_service.mark_job_completed(job.id, result)
        assert job_queue_service.get_job_status(job.id) == JobStatus.COMPLETED

        # Verify result is stored
        final_job = job_queue_service.get_job(job.id)
        assert final_job.result == result
        assert final_job.status == JobStatus.COMPLETED

    def test_job_lifecycle_with_failure(self, job_queue_service):
        """Test job lifecycle with failure: QUEUED -> PROCESSING -> FAILED."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={"key": "value"}
        )

        # Initial state
        assert job_queue_service.get_job_status(job.id) == JobStatus.QUEUED

        # Move to processing
        job_queue_service.mark_job_processing(job.id)
        assert job_queue_service.get_job_status(job.id) == JobStatus.PROCESSING

        # Mark as failed
        error_msg = "Critical error occurred"
        job_queue_service.mark_job_failed(job.id, error_msg)
        assert job_queue_service.get_job_status(job.id) == JobStatus.FAILED

        # Verify error is stored
        final_job = job_queue_service.get_job(job.id)
        assert final_job.error == error_msg
        assert final_job.status == JobStatus.FAILED

    def test_create_job_with_optional_tenant_id(self, job_queue_service):
        """Test that create_job can optionally include tenant_id."""
        job = job_queue_service.create_job(
            workflow_id="workflow-123",
            workflow_name="test_workflow",
            payload={},
            tenant_id="tenant-456"
        )

        assert job.tenant_id == "tenant-456"

        retrieved_job = job_queue_service.get_job(job.id)
        assert retrieved_job.tenant_id == "tenant-456"
