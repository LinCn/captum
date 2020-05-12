#!/usr/bin/env python3

import warnings

import torch


def _divide_and_aggregate_metrics(
    inputs, n_samples, metric_func, agg_func=torch.add, max_examples_per_batch=None
):
    r"""
    This function is used to slice large number of samples `n_samples` per
    input example into smaller pieces, computing the metics for each small piece and
    aggregating the results across all `n_samples` per example. The function
    returns overall aggregated metric per sample. The size of each slice is determined
    by the `max_examples_per_batch` input parameter.

    Args:

        inputs (tuple): The original inputs formatted in a tuple that are passed to
                        the metrics function and that are used to compute the
                        attributions for.
        n_samples (int): The number of samples per example that are used for
                        perturbation purposes for example.
        metric_func (callable): This function takes the number of samples per
                        input batch and returns an overall metric for each example.
        agg_func (callable, optional): This function is used to aggregate the
                        metrics across multiple sub-batches and that are
                        generated by `metric_func`.
        max_examples_per_batch (int, optional): The maximum number of allowed examples
                        per batch.

    """
    device = inputs[0].device
    bsz = inputs[0].size(0)

    if max_examples_per_batch is not None and (
        max_examples_per_batch // bsz < 1 or max_examples_per_batch // bsz > n_samples
    ):
        warnings.warn(
            (
                "`max_examples_per_batch` must be at least equal to the"
                " input batch size and at most to `input batch size` * `n_samples`."
                "`max_examples_per_batch` is: {} and the input batch size is: {}."
                "This is necessary because we require that each sub-batch that is used "
                "to compute the metrics, contains at least an instance of "
                "the original example and doesn't exceed the number of "
                "expanded n_samples."
            ).format(max_examples_per_batch, bsz)
        )

    max_inps_per_batch = (
        n_samples
        if max_examples_per_batch is None
        else min(max(max_examples_per_batch // bsz, 1), n_samples)
    )

    current_n_steps = 0
    metrics_sum = torch.zeros(bsz, device=device)

    while current_n_steps < n_samples:
        current_n_steps += max_inps_per_batch

        metric = metric_func(
            max_inps_per_batch
            if current_n_steps <= n_samples
            else max_inps_per_batch - (current_n_steps - n_samples)
        )

        current_n_steps = min(current_n_steps, n_samples)

        metrics_sum = agg_func(metrics_sum, metric)
    return metrics_sum