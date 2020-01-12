from libspn_keras.backprop_mode import BackpropMode
from libspn_keras.logspace import logspace_wrapper_initializer
from libspn_keras.math.hard_em_grads import logmatmul_hard_em_through_grads_from_accumulators
from libspn_keras.math.logmatmul import logmatmul
from tensorflow import keras
from tensorflow import initializers
import tensorflow as tf

from libspn_keras.math.soft_em_grads import log_softmax_from_accumulators_with_em_grad


class SpatialLocalSum(keras.layers.Layer):
    """
    Computes a spatial local sum, i.e. all cells will have unique weights (no weight sharing
    across spatial access).
    """

    def __init__(
        self, num_sums, logspace_accumulators=False, accumulator_initializer=None,
        backprop_mode=BackpropMode.GRADIENT, **kwargs
    ):
        super(SpatialLocalSum, self).__init__(**kwargs)
        self.num_sums = num_sums
        self.logspace_accumulators = logspace_accumulators
        self.accumulator_initializer = accumulator_initializer or initializers.Constant(1)
        self.backprop_mode = backprop_mode
        self._accumulators = None

    def build(self, input_shape):
        # Create a trainable weight variable for this layer.
        _, num_scopes_vertical, num_scopes_horizontal, num_channels_in = input_shape

        weights_shape = (num_scopes_vertical, num_scopes_horizontal, num_channels_in, self.num_sums)

        initializer = self.accumulator_initializer
        if self.logspace_accumulators:
            initializer = logspace_wrapper_initializer(initializer)

        self._accumulators = self.add_weight(
            name='sum_weights', shape=weights_shape, initializer=initializer)
        super(SpatialLocalSum, self).build(input_shape)

    def call(self, x):

        x_scopes_first = tf.transpose(x, (1, 2, 0, 3))

        log_weights_unnormalized = self._accumulators

        if not self.logspace_accumulators \
                and self.backprop_mode in [BackpropMode.HARD_EM, BackpropMode.HARD_EM_UNWEIGHTED]:
            out_scopes_first = logmatmul_hard_em_through_grads_from_accumulators(
                x_scopes_first, self._accumulators,
                unweighted=self.backprop_mode == BackpropMode.HARD_EM_UNWEIGHTED
            )
            return tf.transpose(out_scopes_first, (2, 0, 1, 3))

        if not self.logspace_accumulators and self.backprop_mode == BackpropMode.EM:
            log_weights_normalized = log_softmax_from_accumulators_with_em_grad(
                self._accumulators, axis=2)
        elif not self.logspace_accumulators:
            log_weights_normalized = tf.nn.log_softmax(
                tf.math.log(log_weights_unnormalized), axis=2)
        else:
            log_weights_normalized = tf.nn.log_softmax(log_weights_unnormalized, axis=2)

        out_scopes_first = logmatmul(x_scopes_first, log_weights_normalized)

        return tf.transpose(out_scopes_first, (2, 0, 1, 3))

    def compute_output_shape(self, input_shape):
        num_batch, num_scopes_vertical, num_scopes_horizontal, _ = input_shape
        return num_batch, num_scopes_vertical, num_scopes_horizontal, self.num_sums
