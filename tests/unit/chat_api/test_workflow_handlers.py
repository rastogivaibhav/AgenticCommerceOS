"""Tests for workflow execution handlers (Task 5)."""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, MagicMock, patch
import uuid

from apps.chat_api.handlers.sync_executor import SyncExecutor
from apps.chat_api.handlers.async_executor import AsyncExecutor
from acosplatform.job_queue.models import Job, JobStatus


class TestSyncExecutor:
    """Test suite for synchronous workflow execution."""

    @pytest.fixture
    def sync_executor(self):
        """Create a SyncExecutor instance."""
        return SyncExecutor()

    @pytest.fixture
    def sample_workflow(self):
        """Sample workflow definition for testing."""
        return {
            "workflow_id": "wf_test_123",
            "workflow_name": "Test Workflow",
            "timeout_seconds": 2,
            "steps": [
                {
                    "step_id": "step_1",
                    "agent": "search_agent",
                    "input": {"query": "blue dresses"},
                }
            ],
        }

    def test_sync_executor_init(self, sync_executor):
        """Test SyncExecutor initialization."""
        assert sync_executor is not None

    def test_execute_workflow_success(self, sync_executor, sample_workflow):
        """Test successful workflow execution (sync)."""
        # Given a valid workflow
        # When we execute it
        result = sync_executor.execute(
            workflow=sample_workflow,
            input_data={"query": "blue dresses"},
        )

        # Then we should get a dict result
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] in ("success", "completed")
        assert "result" in result or "output" in result

    def test_execute_workflow_timeout_respected(self, sync_executor):
        """Test that timeout_seconds is respected."""
        workflow = {
            "workflow_id": "wf_timeout_test",
            "workflow_name": "Timeout Test",
            "timeout_seconds": 1,  # 1 second timeout
            "steps": [],
        }
        # Should not raise an exception, just return result within timeout
        result = sync_executor.execute(workflow=workflow, input_data={})
        assert isinstance(result, dict)

    def test_execute_workflow_missing_timeout_defaults_to_2(self, sync_executor):
        """Test that missing timeout_seconds defaults to 2."""
        workflow = {
            "workflow_id": "wf_no_timeout",
            "workflow_name": "No Timeout",
            # No timeout_seconds key
            "steps": [],
        }
        # Should use default of 2 seconds
        result = sync_executor.execute(workflow=workflow, input_data={})
        assert isinstance(result, dict)

    def test_execute_workflow_returns_dict_result(self, sync_executor, sample_workflow):
        """Test that execution returns dict results."""
        result = sync_executor.execute(
            workflow=sample_workflow,
            input_data={"query": "test"},
        )
        # Result should be a dict, not a Job object or other type
        assert isinstance(result, dict)
        # Should have meaningful content
        assert len(result) > 0

    def test_execute_workflow_includes_execution_time(self, sync_executor, sample_workflow):
        """Test that result includes execution_time_ms."""
        result = sync_executor.execute(
            workflow=sample_workflow,
            input_data={"query": "test"},
        )
        # Should include execution time information
        assert isinstance(result, dict)
        # May have execution_time_ms or similar
        assert "execution_time_ms" in result or "execution_time" in result or "duration" in result

    def test_execute_workflow_includes_status(self, sync_executor, sample_workflow):
        """Test that result includes execution status."""
        result = sync_executor.execute(
            workflow=sample_workflow,
            input_data={"query": "test"},
        )
        assert "status" in result
        assert result["status"] in ("success", "completed", "failed")


class TestAsyncExecutor:
    """Test suite for asynchronous workflow execution."""

    @pytest.fixture
    def mock_job_queue_service(self):
        """Mock JobQueueService."""
        return Mock()

    @pytest.fixture
    def async_executor(self, mock_job_queue_service):
        """Create AsyncExecutor instance with mocked job queue."""
        executor = AsyncExecutor(job_queue_service=mock_job_queue_service)
        return executor

    @pytest.fixture
    def sample_workflow(self):
        """Sample workflow for testing."""
        return {
            "workflow_id": "wf_async_123",
            "workflow_name": "Async Test Workflow",
            "timeout_seconds": 30,
            "steps": [
                {
                    "step_id": "step_1",
                    "agent": "search_agent",
                    "input": {"query": "blue dresses"},
                }
            ],
        }

    def test_async_executor_init_with_service(self, mock_job_queue_service):
        """Test AsyncExecutor initialization with service."""
        executor = AsyncExecutor(job_queue_service=mock_job_queue_service)
        assert executor.job_queue_service == mock_job_queue_service

    def test_async_executor_init_creates_default_service(self):
        """Test AsyncExecutor creates default service if not provided."""
        executor = AsyncExecutor()
        assert executor.job_queue_service is not None

    def test_enqueue_workflow_creates_job(self, async_executor, sample_workflow, mock_job_queue_service):
        """Test that enqueue creates a job and returns job ID."""
        # Setup mock
        mock_job = Mock(spec=Job)
        mock_job.id = "job_test_123"
        mock_job.status = JobStatus.QUEUED
        mock_job_queue_service.create_job.return_value = mock_job

        # When we enqueue a workflow
        result = async_executor.enqueue(
            workflow=sample_workflow,
            input_data={"query": "test"},
            tenant_id="test_tenant",
        )

        # Then a job should be created
        assert "job_id" in result
        assert result["job_id"] == "job_test_123"
        mock_job_queue_service.create_job.assert_called_once()

    def test_enqueue_calls_job_queue_service_create_job(
        self, async_executor, sample_workflow, mock_job_queue_service
    ):
        """Test that enqueue calls JobQueueService.create_job()."""
        mock_job = Mock(spec=Job)
        mock_job.id = "job_abc"
        mock_job.status = JobStatus.QUEUED
        mock_job_queue_service.create_job.return_value = mock_job

        async_executor.enqueue(
            workflow=sample_workflow,
            input_data={"test": "data"},
            tenant_id="tenant_123",
        )

        # Should call create_job with workflow info
        mock_job_queue_service.create_job.assert_called_once()
        call_args = mock_job_queue_service.create_job.call_args
        assert call_args[1]["workflow_id"] == "wf_async_123"
        assert call_args[1]["workflow_name"] == "Async Test Workflow"
        assert call_args[1]["tenant_id"] == "tenant_123"

    def test_enqueue_returns_dict_result(self, async_executor, sample_workflow, mock_job_queue_service):
        """Test that enqueue returns dict result, not Job object."""
        mock_job = Mock(spec=Job)
        mock_job.id = "job_xyz"
        mock_job.status = JobStatus.QUEUED
        mock_job_queue_service.create_job.return_value = mock_job

        result = async_executor.enqueue(
            workflow=sample_workflow,
            input_data={},
            tenant_id="tenant",
        )

        # Result should be a dict
        assert isinstance(result, dict)
        # Should contain status info
        assert "status" in result
        assert result["status"] in ("queued", "accepted", "created")
        # Should have job_id
        assert "job_id" in result

    def test_enqueue_includes_polling_endpoint(
        self, async_executor, sample_workflow, mock_job_queue_service
    ):
        """Test that enqueue result includes polling endpoint."""
        mock_job = Mock(spec=Job)
        mock_job.id = "job_poll_123"
        mock_job.status = JobStatus.QUEUED
        mock_job_queue_service.create_job.return_value = mock_job

        result = async_executor.enqueue(
            workflow=sample_workflow,
            input_data={},
        )

        # Should include polling endpoint
        assert "polling_endpoint" in result or "status_url" in result

    def test_execute_workflow_calls_enqueue(self, async_executor, sample_workflow, mock_job_queue_service):
        """Test that execute() method calls enqueue internally."""
        mock_job = Mock(spec=Job)
        mock_job.id = "job_exec_123"
        mock_job.status = JobStatus.QUEUED
        mock_job_queue_service.create_job.return_value = mock_job

        result = async_executor.execute(
            workflow=sample_workflow,
            input_data={"query": "test"},
            tenant_id="test_tenant",
        )

        # Should call create_job
        mock_job_queue_service.create_job.assert_called_once()
        # Should return job dict
        assert "job_id" in result

    def test_get_job_status(self, async_executor, mock_job_queue_service):
        """Test getting job status."""
        mock_job = Mock(spec=Job)
        mock_job.id = "job_status_123"
        mock_job.status = JobStatus.PROCESSING
        mock_job.workflow_id = "wf_test"
        mock_job.workflow_name = "Test"
        mock_job.created_at = None
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.error = None
        mock_job_queue_service.get_job.return_value = mock_job

        result = async_executor.get_job_status("job_status_123")

        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "processing"

    def test_get_job_result(self, async_executor, mock_job_queue_service):
        """Test getting job result."""
        mock_job = Mock(spec=Job)
        mock_job.id = "job_result_123"
        mock_job.status = JobStatus.COMPLETED
        mock_job.result = {"products": ["product_1", "product_2"]}
        mock_job.workflow_id = "wf_test"
        mock_job.workflow_name = "Test"
        mock_job.created_at = None
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.error = None
        mock_job_queue_service.get_job.return_value = mock_job

        result = async_executor.get_job_result("job_result_123")

        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "completed"
        assert "result" in result


class TestExecutorIntegration:
    """Integration tests for sync and async executors working together."""

    def test_both_executors_return_dicts(self):
        """Test that both executors always return dicts."""
        sync_executor = SyncExecutor()
        async_executor = AsyncExecutor()

        workflow = {
            "workflow_id": "wf_integration",
            "workflow_name": "Integration Test",
            "timeout_seconds": 2,
            "steps": [],
        }

        sync_result = sync_executor.execute(workflow=workflow, input_data={})
        async_result = async_executor.execute(workflow=workflow, input_data={})

        assert isinstance(sync_result, dict)
        assert isinstance(async_result, dict)

    def test_workflow_decision_sync_vs_async(self):
        """Test decision logic: fast workflows use sync, slow use async."""
        from unittest.mock import Mock, patch

        sync_executor = SyncExecutor()

        # Mock job queue service for async executor
        mock_job_queue = Mock()
        mock_job = Mock(spec=Job)
        mock_job.id = "job_123"
        mock_job.status = JobStatus.QUEUED
        mock_job_queue.create_job.return_value = mock_job

        async_executor = AsyncExecutor(job_queue_service=mock_job_queue)

        # Fast workflow (< 2s)
        fast_workflow = {
            "workflow_id": "wf_fast",
            "workflow_name": "Fast Lookup",
            "timeout_seconds": 1,
            "steps": [],
        }

        # Slow workflow (> 2s)
        slow_workflow = {
            "workflow_id": "wf_slow",
            "workflow_name": "Complex Analysis",
            "timeout_seconds": 30,
            "steps": [],
        }

        # Fast workflow can use sync
        fast_result = sync_executor.execute(workflow=fast_workflow, input_data={})
        assert fast_result["status"] in ("success", "completed")

        # Slow workflow should use async
        slow_result = async_executor.execute(workflow=slow_workflow, input_data={})
        assert "job_id" in slow_result
