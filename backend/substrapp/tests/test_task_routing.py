from parameterized import parameterized
import mock
import uuid

from django.db.utils import IntegrityError
from django.test import TestCase

from substrapp.task_routing import _get_workers_with_fewest_running_cps, release_worker
from substrapp.models.computeplan_worker_mapping import ComputePlanWorkerMapping


class ComputePlanWorkerMappingAttachAndReleaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # initial set up with two workers and one compute plan attached to worker 0
        cls.compute_plan_a_key = uuid.uuid4()
        cls.worker_0_index = 0
        cls.worker_1_index = 1

        cls.mapping_a = cls._attach_cp_to_worker(cls.compute_plan_a_key, cls.worker_0_index)

    @staticmethod
    def _attach_cp_to_worker(compute_plan_key, worker_index):
        return ComputePlanWorkerMapping.objects.create(
            compute_plan_key=compute_plan_key,
            worker_index=worker_index
        )

    def test_cp_not_attached_to_two_workers_at_the_same_time(self):
        with self.assertRaises(IntegrityError):
            self._attach_cp_to_worker(self.compute_plan_a_key, self.worker_1_index)

    def test_cp_attached_to_one_worker_after_first_release_ok(self):
        release_worker(self.compute_plan_a_key)
        self._attach_cp_to_worker(self.compute_plan_a_key, self.worker_1_index)

    def test_create_release_date_on_worker_release(self):
        self.assertIsNone(self.mapping_a.release_date)

        release_worker(self.compute_plan_a_key)
        mapping = ComputePlanWorkerMapping.objects.get(
            compute_plan_key=self.compute_plan_a_key,
        )
        self.assertIsNotNone(mapping.release_date)


class TaskRoutingTests(TestCase):
    @parameterized.expand(
        [
            (
                "3 workers, no CP running",
                3,
                [],
                [0, 1, 2],
            ),
            (
                "3 workers, 2 CPs running on worker 0, 1 CP running on worker 1, 2 CPs running on worker 2",
                3,
                [
                    ComputePlanWorkerMapping(worker_index=0, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=2, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=0, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=1, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=2, compute_plan_key=uuid.uuid4()),
                ],
                [1],
            ),
            (
                "3 workers, 3 CPs running on worker 0, 1 CP running on worker 1, 1 CPs running on worker 2",
                3,
                [
                    ComputePlanWorkerMapping(worker_index=0, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=2, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=0, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=1, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=0, compute_plan_key=uuid.uuid4()),
                ],
                [1, 2],
            ),
            (
                "4 workers, 2 CPs running on worker 0, 1 CP running on worker 1, 2 CPs running on worker 2",
                4,
                [
                    ComputePlanWorkerMapping(worker_index=0, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=2, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=0, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=1, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=2, compute_plan_key=uuid.uuid4()),
                ],
                [3],
            ),
            (
                "3 workers, 1 CP running on each worker",
                3,
                [
                    ComputePlanWorkerMapping(worker_index=0, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=2, compute_plan_key=uuid.uuid4()),
                    ComputePlanWorkerMapping(worker_index=1, compute_plan_key=uuid.uuid4()),
                ],
                [0, 1, 2],
            ),
        ]
    )
    def test_get_workers_with_fewest_running_cps(self, _, num_workers, all_mappings, expected):
        for mapping in all_mappings:
            mapping.save()

        with mock.patch('substrapp.task_routing.get_worker_replica_set_scale') as m_replica_scale:
            m_replica_scale.return_value = num_workers
            actual = _get_workers_with_fewest_running_cps()
            self.assertEqual(sorted(actual), expected)
