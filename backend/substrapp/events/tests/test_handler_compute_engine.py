import pytest
from pytest_mock import MockerFixture

import orchestrator
import orchestrator.mock as orc_mock
from substrapp.events import handler_compute_engine


@pytest.mark.parametrize(
    "test_input,expected_result",
    [
        pytest.param([orc_mock.ComputeTaskInputFactory(asset_key="my_asset")], [], id="no parent-task input"),
        pytest.param(
            [
                orc_mock.ComputeTaskInputFactory(asset_key=None, parent_task_key="parent_task"),
                orc_mock.ComputeTaskInputFactory(asset_key=None, parent_task_key="parent_task_2"),
            ],
            [
                orc_mock.ComputeTaskInputFactory(asset_key=None, parent_task_key="parent_task"),
                orc_mock.ComputeTaskInputFactory(asset_key=None, parent_task_key="parent_task_2"),
            ],
            id="parent-task input",
        ),
        pytest.param(
            [
                orc_mock.ComputeTaskInputFactory(asset_key="my_asset"),
                orc_mock.ComputeTaskInputFactory(asset_key=None, parent_task_key="parent_task_2"),
            ],
            [
                orc_mock.ComputeTaskInputFactory(asset_key=None, parent_task_key="parent_task_2"),
            ],
            id="non parent task and parent task",
        ),
    ],
)
def test_filter_parent_task_outputs_refs(
    test_input: list[orchestrator.ComputeTaskInput], expected_result: list[orchestrator.ComputeTaskInput]
):
    res = handler_compute_engine._filter_parent_task_outputs_refs(test_input)
    assert list(res) == expected_result


class TestMapProducerToInput:
    def test_valid_inputs(self, mocker: MockerFixture):
        task_inputs = [
            orc_mock.ComputeTaskInputFactory(parent_task_key="my_task", parent_task_output_identifier="id1"),
            orc_mock.ComputeTaskInputFactory(parent_task_key="my_other_task", parent_task_output_identifier="id2"),
        ]
        orc_client = mocker.Mock()
        orc_client.query_task.side_effect = [
            orc_mock.ComputeTaskFactory(key="my_task"),
            orc_mock.ComputeTaskFactory(key="my_other_task"),
        ]

        mappings = list(handler_compute_engine._map_producer_to_input(orc_client, task_inputs))

        orc_client.query_task.assert_any_call("my_task")
        orc_client.query_task.assert_any_call("my_other_task")
        assert orc_client.query_task.call_count == 2
        assert len(mappings) == 2
        assert mappings[0][0] == "id1"
        assert mappings[0][1].key == "my_task"

    def test_invalid_input(self, mocker: MockerFixture):
        task_inputs = [orc_mock.ComputeTaskInputFactory(asset_key="test")]
        orc_client = mocker.Mock()

        with pytest.raises(TypeError):
            list(handler_compute_engine._map_producer_to_input(orc_client, task_inputs))


def test_filter_outputs_generated_by_worker():
    worker = "my_worker"
    map1 = ("id1", orc_mock.ComputeTaskFactory(worker="my_worker"))
    map2 = ("id2", orc_mock.ComputeTaskFactory(worker="another_worker"))
    map3 = ("id1", orc_mock.ComputeTaskFactory(worker="my_worker"))
    input_mapping = [map1, map2, map3]
    expected_result = [map1, map3]

    res = list(handler_compute_engine._filter_outputs_generated_by_worker(input_mapping, worker))
    assert res == expected_result


def test_filter_transient_outputs():
    id1 = orc_mock.ComputeTaskOutputFactory(transient=True)
    id2 = orc_mock.ComputeTaskOutputFactory(transient=False)

    task_1 = orc_mock.ComputeTaskFactory(outputs={"id1": id1})
    task_2 = orc_mock.ComputeTaskFactory(outputs={"id2": id2})

    input_data = [("id1", task_1), ("id2", task_2)]
    expected_result = [("id1", task_1.key)]

    res = list(handler_compute_engine._filter_transient_outputs(input_data))
    assert res == expected_result


def test_get_deletable_task_outputs(mocker: MockerFixture):
    task_inputs = [
        orc_mock.ComputeTaskInputFactory(parent_task_key="parent_task", parent_task_output_identifier="id1"),
        orc_mock.ComputeTaskInputFactory(parent_task_key="parent_task_2", parent_task_output_identifier="id3"),
        orc_mock.ComputeTaskInputFactory(asset_key="my_model"),
        orc_mock.ComputeTaskInputFactory(parent_task_key="parent_task", parent_task_output_identifier="id2"),
    ]
    orc_client = mocker.Mock()
    handler_compute_engine._MY_ORGANIZATION = "my_worker"

    id1 = orc_mock.ComputeTaskOutputFactory(transient=True)
    id2 = orc_mock.ComputeTaskOutputFactory(transient=False)
    id3 = orc_mock.ComputeTaskOutputFactory(transient=False)

    parent_task = orc_mock.ComputeTaskFactory(key="parent_task", outputs={"id1": id1, "id2": id2}, worker="my_worker")
    parent_task_2 = orc_mock.ComputeTaskFactory(key="parent_task_2", outputs={"id3": id3}, worker="other_worker")

    orc_client.query_task.side_effect = [parent_task, parent_task_2, parent_task]

    expected_result = [("id1", parent_task.key)]

    res = handler_compute_engine._get_deletable_task_outputs(orc_client, task_inputs)

    assert res == expected_result


def test_handle_task_outputs(mocker: MockerFixture):
    task_inputs = [
        orc_mock.ComputeTaskInputFactory(parent_task_key="parent_task", parent_task_output_identifier="id1"),
        orc_mock.ComputeTaskInputFactory(parent_task_key="parent_task_2", parent_task_output_identifier="id3"),
        orc_mock.ComputeTaskInputFactory(asset_key="my_model"),
        orc_mock.ComputeTaskInputFactory(parent_task_key="parent_task", parent_task_output_identifier="id2"),
    ]
    orc_client = mocker.Mock()
    m_schedule_task = mocker.patch("substrapp.events.handler_compute_engine.queue_disable_transient_outputs")
    handler_compute_engine._MY_ORGANIZATION = "my_worker"

    id1 = orc_mock.ComputeTaskOutputFactory(transient=True)
    id2 = orc_mock.ComputeTaskOutputFactory(transient=False)
    id3 = orc_mock.ComputeTaskOutputFactory(transient=False)

    parent_task = orc_mock.ComputeTaskFactory(key="parent_task", outputs={"id1": id1, "id2": id2}, worker="my_worker")
    parent_task_2 = orc_mock.ComputeTaskFactory(key="parent_task_2", outputs={"id3": id3}, worker="other_worker")

    orc_client.query_task.side_effect = [parent_task, parent_task_2, parent_task]

    handler_compute_engine._handle_task_outputs(orc_client, "mychannel", task_inputs)
    m_schedule_task.assert_called_once()


def test_handle_finished_task(mocker: MockerFixture):
    orc_client = mocker.Mock()
    task = orc_mock.ComputeTaskFactory(status=orchestrator.ComputeTaskStatus.STATUS_DONE)
    m_handle_task_outputs = mocker.patch("substrapp.events.handler_compute_engine._handle_task_outputs")

    handler_compute_engine.handle_finished_tasks(orc_client, "mychannel", task)

    m_handle_task_outputs.assert_called_once_with(orc_client, "mychannel", [])


class TestHandleDisabledModel:
    def test_disable_foreign_model(self, mocker: MockerFixture):
        m_queue_remove_intermediary_model = mocker.patch(
            "substrapp.events.handler_compute_engine.queue_remove_intermediary_models_from_buffer"
        )
        model = orc_mock.ModelFactory(owner="notme")
        handler_compute_engine.handle_disabled_model("mychannel", model)

        m_queue_remove_intermediary_model.assert_called_once_with(model.key)

    def test_disable_local_model(self, mocker: MockerFixture):
        m_queue_remove_intermediary_model_ab = mocker.patch(
            "substrapp.events.handler_compute_engine.queue_remove_intermediary_models_from_buffer"
        )
        m_queue_remove_intermediary_model_db = mocker.patch(
            "substrapp.events.handler_compute_engine.queue_remove_intermediary_models_from_db_new"
        )
        model = orc_mock.ModelFactory(owner="my_worker")
        handler_compute_engine._MY_ORGANIZATION = "my_worker"
        handler_compute_engine.handle_disabled_model("mychannel", model)

        m_queue_remove_intermediary_model_ab.assert_called_once_with(model.key)
        m_queue_remove_intermediary_model_db.assert_called_once_with("mychannel", model.key)
