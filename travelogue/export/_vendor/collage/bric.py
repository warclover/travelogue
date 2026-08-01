
import numpy as np

from .layout import BalancedLayout, GridLayout, Layout, Position, Size


def fit_pictures_balanced(
    image_sizes,
    layout="horizontal",
    width=None,
    border=0,
    spacing=0,
    round_result=False,
) -> tuple[list[Size], list[Position], Size]:
    if round_result:
        assert isinstance(border, int)
        assert isinstance(spacing, int)

    image_sizes = [Size(w, h) for w, h in image_sizes]
    layout = BalancedLayout(
        len(image_sizes),
        horizontal_root=(layout == "horizontal"),
        width=width,
        border=border,
        spacing=spacing,
    )

    return fit_pictures(image_sizes, layout, round_result)


def fit_pictures_grid(
    image_sizes,
    *,
    cols=None,
    rows=None,
    width=None,
    border=0,
    spacing=0,
    round_result=False
) -> tuple[list[Size], list[Position], Size]:
    image_sizes = [Size(w, h) for w, h in image_sizes]
    layout = GridLayout(
        len(image_sizes),
        cols=cols,
        rows=rows,
        width=width,
        border=border,
        spacing=spacing,
    )

    return fit_pictures(image_sizes, layout, round_result)


def fit_pictures(image_sizes: list[Size], layout: Layout, round_result=False) -> tuple[list[Size], list[Position], Size]:
    if round_result:
        # AC-GCS-11 · the integer path pulls python-mip (GPL); callers use the
        # float solve and round locally. Refuse instead of importing mip.
        raise RuntimeError("MIP/integer path disabled (AC-GCS-11)")

    new_sizes = _compute_rescaled_image_sizes(image_sizes, layout)

    positions, canvas_size = layout.compute_positions(new_sizes)

    return new_sizes, positions, canvas_size


def _compute_rescaled_image_sizes(image_sizes: list[Size], layout: Layout) -> list[Size]:
    constraints = layout.get_constraints(image_sizes)

    # set up and a linear equation system from the constraints, and solve it
    n_images = len(image_sizes)
    n_constraints = len(constraints)

    aspect_ratios = np.array([h/w for w, h in image_sizes])
    A = np.zeros((n_constraints, n_images))  # constraints matrix
    b = np.zeros(n_constraints)  # rhs of equation Aw = b

    for c_idx, c in enumerate(constraints):
        for img_idx in c.positive_ids:
            A[c_idx, img_idx] = aspect_ratios[img_idx] if c.is_height else 1

        for img_idx in c.negative_ids:
            A[c_idx, img_idx] = -(aspect_ratios[img_idx] if c.is_height else 1)

        b[c_idx] = c.result

    new_widths = np.linalg.solve(A, b)
    new_heights = aspect_ratios * new_widths

    new_sizes = [Size(w, h) for w, h in zip(new_widths, new_heights)]

    return new_sizes


def _compute_integer_image_sizes(image_sizes: list[Size], layout: Layout) -> list[Size]:
    # AC-GCS-11 · disabled: the upstream integer solve depended on the GPL
    # python-mip package. It is intentionally not imported; callers must use the
    # float path (_compute_rescaled_image_sizes) and round locally.
    raise RuntimeError("MIP/integer path disabled (AC-GCS-11)")
