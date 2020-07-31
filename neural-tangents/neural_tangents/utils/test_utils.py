# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for testing."""


import logging

import dataclasses
from jax.lib import xla_bridge
import jax.test_util as jtu
from .kernel import Kernel
import numpy as onp

from absl.testing import parameterized
import tensorflow as tf
from tensorflow.python.ops import numpy_ops as np
import sys
from extensions import jit
from tensorflow import vectorized_map as vmap


def _jit_vmap(f):
  return jit(vmap(f))


def update_test_tolerance(f32_tol=5e-3, f64_tol=1e-5):
  jtu._default_tolerance[onp.dtype(onp.float32)] = f32_tol
  jtu._default_tolerance[onp.dtype(onp.float64)] = f64_tol
  def default_tolerance():
    if jtu.device_under_test() != 'tpu':
      return jtu._default_tolerance
    tol = jtu._default_tolerance.copy()
    tol[onp.dtype(onp.float32)] = 5e-2
    return tol
  jtu.default_tolerance = default_tolerance


def stub_out_pmap(batch, count):
  # If we are using GPU or CPU stub out pmap with vmap to simulate multi-core.
  if count > 0:

    class xla_bridge_stub(object):

      def device_count(self):
        return count

    platform = xla_bridge.get_backend().platform
    if platform == 'gpu' or platform == 'cpu':
      batch.pmap = _jit_vmap
      batch.xla_bridge = xla_bridge_stub()


def _log(relative_error, expected, actual, did_pass):
  msg = 'PASSED' if did_pass else 'FAILED'
  logging.info(f'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n'
               f'\n{msg} with {relative_error} relative error: \n'
               f'---------------------------------------------\n'
               f'EXPECTED: \n'
               f'{expected}\n'
               f'---------------------------------------------\n'
               f'ACTUAL: \n'
               f'{actual}\n'
               f'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n'
               )


def assert_close_matrices(self, expected, actual, rtol):
  self.assertEqual(expected.shape, actual.shape)
  relative_error = (
      np.linalg.norm(actual - expected) /
      np.maximum(np.linalg.norm(expected), 1e-12))
  if relative_error > rtol or np.isnan(relative_error):
    _log(relative_error, expected, actual, False)
    self.fail(self.failureException('Relative ERROR: ',
                                    float(relative_error),
                                    'EXPECTED:' + ' ' * 50,
                                    expected,
                                    'ACTUAL:' + ' ' * 50,
                                    actual))
  else:
    _log(relative_error, expected, actual, True)


class NeuralTangentsTestCase(tf.test.TestCase, parameterized.TestCase):

  def assertAllClose(
      self,
      x,
      y,
      *,
      check_dtypes=True,
      atol=None,
      rtol=None,
      canonicalize_dtypes=True):
    atol = atol if atol is not None else 1e-06
    rtol = rtol if rtol is not None else 1e-06
    if isinstance(x, Kernel):
      self.assertIsInstance(y, Kernel)
      x_dict = {
        "nngp": x.nngp,
        "ntk": x.ntk,
        "cov1": x.cov1,
        "cov2": x.cov2,
        "x1_is_x2": x.x1_is_x2,
        "is_gaussian": x.is_gaussian,
        "is_reversed": x.is_reversed,
        "is_input": x.is_input,
        "diagonal_batch": x.diagonal_batch,
        "diagonal_spatial": x.diagonal_spatial,
        "shape1": x.shape1,
        "shape2": x.shape2,
        "batch_axis": x.batch_axis,
        "channel_axis": x.channel_axis,
        "mask1": x.mask1,
        "mask2": x.mask2
      }
      y_dict = {
        "nngp": y.nngp,
        "ntk": y.ntk,
        "cov1": y.cov1,
        "cov2": y.cov2,
        "x1_is_x2": y.x1_is_x2,
        "is_gaussian": y.is_gaussian,
        "is_reversed": y.is_reversed,
        "is_input": y.is_input,
        "diagonal_batch": y.diagonal_batch,
        "diagonal_spatial": y.diagonal_spatial,
        "shape1": y.shape1,
        "shape2": y.shape2,
        "batch_axis": y.batch_axis,
        "channel_axis": y.channel_axis,
        "mask1": y.mask1,
        "mask2": y.mask2
      }
      for field in dataclasses.fields(Kernel):
        is_pytree_node = field.metadata.get('pytree_node', True)
        if is_pytree_node and not (x_dict[field.name] is None or y_dict[field.name] is None):
          super().assertAllClose(
              x_dict[field.name], y_dict[field.name], atol=atol, rtol=rtol)
        else:
          super().assertAllEqual(x_dict[field.name], y_dict[field.name])
    else:
      return super().assertAllClose(
          onp.array(x), onp.array(y), atol=atol, rtol=rtol)
