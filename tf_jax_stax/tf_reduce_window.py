# Copyright 2020 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


"""
`reduce_window` realization for TensorFlow 2.x.

Zhibo Zhang, 2020.06.15

(Note: Although there is already an XLA ReduceWindow implementation -
<https://www.tensorflow.org/xla/operation_semantics#reducewindow>, in order to
enable backpropagation and better interact with the TF ecosystem, an
implementation that directly builds on `tf.nn` is required.)
"""

import tensorflow as tf
from tensorflow.nn import pool
from trax.tf_numpy import numpy as np
import numpy as onp


def reduce_window(input, init_value, reducer, window_dimensions, strides, padding):
  if reducer not in [np.max, np.add]:
    raise TypeError("Only max pooling and average/sum pooling are supported.")
  pooling_type = "AVG" if reducer is np.max else "MAX"
  # raise TypeError("input shape: {}, window_dimensions: {}, strides: {}".format(input.shape, window_dimensions, strides))

  # Note that there is no need to send in the parameter data format since the
  # input is already of default data format - "N...C". The adjustments of the
  # input shape is already finished in apply_fun of Pooling in stax.
  output = pool(input, window_dimensions, pooling_type, strides, padding)
  if pooling_type == "MAX":
    return output
  # If it is max pooling, mutiply the output by the number of grids inside a
  # window.
  grids = onp.prod(list(window_dimensions))
  return output * grids
