import pytest

import numpy as np
import torch

from nnsmith.materialize import TestCase
from nnsmith.materialize.onnx import ONNXModel
from nnsmith.graph_gen import random_model_gen, concretize_graph, make_schedule

TestCase.__test__ = False  # supress PyTest warning


def test_onnx_load_dump(tmp_path):
    d = tmp_path / "test_onnx_load_dump"
    d.mkdir()

    gen = random_model_gen(
        opset=ONNXModel.operators(),
        init_rank=4,
        seed=54341,
        max_nodes=5,
    )

    fixed_graph, concrete_abstensors = concretize_graph(
        gen.abstract_graph, gen.tensor_dataflow, gen.get_solutions()
    )

    schedule = make_schedule(fixed_graph, concrete_abstensors)

    model = ONNXModel.from_schedule(schedule)

    assert model.with_torch

    model.refine_weights()  # either random generated or gradient-based.
    oracle = model.make_oracle()

    testcase = TestCase(model, oracle)
    testcase.dump(root_folder=d)

    loaded_testcase = TestCase.load(model_type=type(model), root_folder=d)

    def compare_two_oracle(src, loaded):
        assert len(loaded.input) == len(src.input)
        assert len(loaded.output) == len(src.output)
        for k, v in loaded.input.items():
            assert np.allclose(v, src.input[k], equal_nan=True)
        for k, v in loaded.output.items():
            assert np.allclose(v, src.output[k], equal_nan=True)

    # check oracle
    compare_two_oracle(oracle, loaded_testcase.oracle)

    loaded_model = loaded_testcase.model.torch_model
    loaded_model.sat_inputs = {k: torch.from_numpy(v) for k, v in oracle.input.items()}
    rerun_oracle = loaded_model.make_oracle()
    compare_two_oracle(oracle, rerun_oracle)


def test_bug_report_load_dump(tmp_path):
    d = tmp_path / "test_onnx_load_dump"
    d.mkdir()

    gen = random_model_gen(
        opset=ONNXModel.operators(),
        init_rank=4,
        seed=5341,
        max_nodes=5,
    )

    fixed_graph, concrete_abstensors = concretize_graph(
        gen.abstract_graph, gen.tensor_dataflow, gen.get_solutions()
    )

    schedule = make_schedule(fixed_graph, concrete_abstensors)

    model = ONNXModel.from_schedule(schedule)

    assert model.with_torch

    model.refine_weights()  # either random generated or gradient-based.
    oracle = model.make_oracle()

    testcase = TestCase(model, oracle)
    testcase.dump(root_folder=d)

    loaded_testcase = TestCase.load(model_type=type(model), root_folder=d)

    def compare_two_oracle(src, loaded):
        assert len(loaded.input) == len(src.input)
        assert len(loaded.output) == len(src.output)
        for k, v in loaded.input.items():
            assert np.allclose(v, src.input[k], equal_nan=True)
        for k, v in loaded.output.items():
            assert np.allclose(v, src.output[k], equal_nan=True)

    # check oracle
    compare_two_oracle(oracle, loaded_testcase.oracle)

    loaded_model = loaded_testcase.model.torch_model
    loaded_model.sat_inputs = {k: torch.from_numpy(v) for k, v in oracle.input.items()}
    rerun_oracle = loaded_model.make_oracle()
    compare_two_oracle(oracle, rerun_oracle)