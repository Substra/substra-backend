from substrapp.tasks import tasks_outputs


def test_remove_transient_outputs(mocker):
    orc_client = mocker.Mock()

    deletable_outputs = [("id1", "task1"), ("id2", "task1")]

    tasks_outputs._remove_transient_outputs(orc_client, deletable_outputs)

    orc_client.disable_task_output.assert_any_call("task1", "id1")
    orc_client.disable_task_output.assert_any_call("task1", "id2")
