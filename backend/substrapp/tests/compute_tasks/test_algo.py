from substrapp.compute_tasks.algo import Algo


def test_algo_container_tag(algo: Algo):
    tag = algo.container_image_tag

    assert tag == "algo-f2ca1bb6c7e907d0"
