from tensorflow_probability.python.internal.reparameterization import NOT_REPARAMETERIZED
from libspn_keras.layers.base_leaf import BaseLeaf
from tensorflow_probability import distributions
import tensorflow as tf


class _Indicator(distributions.Distribution):

    def __init__(self, num_components, dtype=tf.int32, name='Indicator'):
        self._num_components = num_components
        super(_Indicator, self).__init__(
            dtype=dtype, name=name, reparameterization_type=NOT_REPARAMETERIZED, allow_nan_stats=True,
            validate_args=False)

    def _log_prob(self, value):
        return tf.squeeze(tf.one_hot(value, depth=self._num_components, on_value=0.0, off_value=float('-inf')), axis=3)


class IndicatorLeaf(BaseLeaf):

    def __init__(self, num_components, dtype=tf.int32):
        super().__init__(num_components, dtype=dtype)

    def _build_distribution(self):
        return _Indicator(self._num_components, dtype=self.dtype)
