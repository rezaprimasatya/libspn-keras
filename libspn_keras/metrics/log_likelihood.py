from tensorflow import keras
import tensorflow as tf


class LogMarginal(keras.metrics.Mean):
    """
    Computes log marginal log(p(X)) assuming that the input is the root of an SPN. It ignore the
    y_true argument, as a target for Y is absent in generative learning.
    """

    def __init__(self, name='log_marginal', **kwargs):
        super(LogMarginal, self).__init__(name=name, **kwargs)

    def update_state(self, _, y_pred, sample_weight=None):
        values = tf.reduce_logsumexp(y_pred, axis=-1)
        return super(LogMarginal, self).update_state(values, sample_weight=sample_weight)
