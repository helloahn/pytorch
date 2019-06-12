from torch import device
from torch._C import default_cuda_generators
from . import _lazy_init, _lazy_call, device_count, device as device_ctx_manager, current_device

__all__ = ['get_rng_state', 'get_rng_state_all',
           'set_rng_state', 'set_rng_state_all',
           'manual_seed', 'manual_seed_all',
           'seed', 'seed_all', 'initial_seed']


def get_rng_state(device=device('cuda')):
    r"""Returns the random number generator state of the current
    GPU as a ByteTensor.

    Args:
        device (torch.device or int, optional): The device to return the RNG state of.
            Default: ``torch.device('cuda')`` (i.e., the current CUDA device).

    .. warning::
        This function eagerly initializes CUDA.
    """
    _lazy_init()
    with device_ctx_manager(device):
        idx = device.index
        if idx is None:
            idx = current_device()
        default_generator = default_cuda_generators[idx]
        return default_generator.get_state()


def get_rng_state_all():
    r"""Returns a tuple of ByteTensor representing the random number states of all devices."""

    results = []
    for i in range(device_count()):
        with device_ctx_manager(i):
            results.append(get_rng_state())
    return results


def set_rng_state(new_state, device=device('cuda')):
    r"""Sets the random number generator state of the current GPU.

    Args:
        new_state (torch.ByteTensor): The desired state
        device (torch.device or int, optional): The device to set the RNG state.
            Default: ``torch.device('cuda')`` (i.e., the current CUDA device).
    """

    # NB: What if device=-1?  You might be afraid that the "current"
    # device would change by the time we actually get around to invoking
    # the lazy callback.  But actually, this is not possible: changing
    # the current device involves a CUDA call, which would in turn
    # initialize the state.  So then _lazy_call would execute cb
    # immediately.
    def cb():
        with device_ctx_manager(device):
            idx = device.index
            if idx is None:
                idx = current_device()
            default_generator = default_cuda_generators[idx]
            default_generator.set_state(new_state)

    _lazy_call(cb)


def set_rng_state_all(new_states):
    r"""Sets the random number generator state of all devices.

    Args:
        new_state (tuple of torch.ByteTensor): The desired state for each device"""
    for i, state in enumerate(new_states):
        set_rng_state(state, i)


def manual_seed(seed):
    r"""Sets the seed for generating random numbers for the current GPU.
    It's safe to call this function if CUDA is not available; in that
    case, it is silently ignored.

    Args:
        seed (int): The desired seed.

    .. warning::
        If you are working with a multi-GPU model, this function is insufficient
        to get determinism.  To seed all GPUs, use :func:`manual_seed_all`.
    """
    seed = int(seed)

    def cb():
        idx = current_device()
        default_generator = default_cuda_generators[idx]
        default_generator.manual_seed(seed)

    _lazy_call(cb)


def manual_seed_all(seed):
    r"""Sets the seed for generating random numbers on all GPUs.
    It's safe to call this function if CUDA is not available; in that
    case, it is silently ignored.

    Args:
        seed (int): The desired seed.
    """
    seed = int(seed)

    def cb():
        for i in range(device_count()):
            with device_ctx_manager(i):
                default_generator = default_cuda_generators[i]
                default_generator.manual_seed(seed)

    _lazy_call(cb)


def seed():
    r"""Sets the seed for generating random numbers to a random number for the current GPU.
    It's safe to call this function if CUDA is not available; in that
    case, it is silently ignored.

    .. warning::
        If you are working with a multi-GPU model, this function will only initialize
        the seed on one GPU.  To initialize all GPUs, use :func:`seed_all`.
    """
    def cb():
        idx = current_device()
        default_generator = default_cuda_generators[idx]
        default_generator.seed()

    _lazy_call(cb)


def seed_all():
    r"""Sets the seed for generating random numbers to a random number on all GPUs.
    It's safe to call this function if CUDA is not available; in that
    case, it is silently ignored.
    """
    def cb():
        random_seed = 0
        seeded = False
        for i in range(device_count()):
            with device_ctx_manager(i):
                default_generator = default_cuda_generators[i]
                if not seeded:
                    default_generator.seed()
                    random_seed = default_generator.initial_seed()
                    seeded = True
                else:
                    default_generator.manual_seed(random_seed)

    _lazy_call(cb)


def initial_seed():
    r"""Returns the current random seed of the current GPU.

    .. warning::
        This function eagerly initializes CUDA.
    """
    _lazy_init()
    idx = current_device()
    default_generator = default_cuda_generators[idx]
    return default_generator.initial_seed()
