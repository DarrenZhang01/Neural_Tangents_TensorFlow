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
Helper:
  Convert the shape to a standard tuple if it not already is.

Zhibo Zhang
"""

import tensorflow as tf
from tensorflow.python.ops import numpy_ops as np
import numpy as onp
import sys


def shape_conversion(shape):
  if isinstance(shape, np.ndarray) or isinstance(shape, tf.TensorSpec):
    return shape.shape
  elif isinstance(shape, tuple):
    # Iterate through all the elements inside the tuple and convert the potential
    # TF Tensor object into shape integers
    shape = list(shape)
    for i in range(len(shape)):
      if isinstance(shape[i], tf.TensorShape):
        shape[i] = tuple(shape[i].as_list())
      elif isinstance(shape[i], np.ndarray):
        shape[i] = shape[i].shape
    # output_shape = tuple([int_ for shape_ in shape for int_ in shape_])
    return tuple(shape)
  elif isinstance(shape, tf.TensorShape):
    return tuple(shape.as_list())
  else:
    return tuple(shape) if isinstance(shape, list) else shape
