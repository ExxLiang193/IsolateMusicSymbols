print("Loading libraries...")
import argparse
import json
from time import time

import cv2
import numpy as np
from joblib import Parallel, delayed
from numpy.lib.stride_tricks import sliding_window_view
from definitions import BaseConfig


class DEFAULTS:
    CONFIG_FILE_PATH = "config.json"


def prepare_image(image_name: str, blur_kernel_size: int, threshold: int, bin_scale: bool = True) -> np.ndarray:
    # Load image as 2D grayscale
    base_image = cv2.imread(image_name, cv2.IMREAD_GRAYSCALE)
    # Maximize contrast
    base_image = cv2.convertScaleAbs(base_image, alpha=3.0, beta=0.0)
    # Blur the image slightly if details are too fine
    base_image = cv2.GaussianBlur(base_image, (blur_kernel_size, blur_kernel_size), cv2.BORDER_DEFAULT)
    # Convert to black-and-white image (i.e. values are either 0 or 255)
    base_image = cv2.threshold(base_image, threshold, 255, cv2.THRESH_BINARY)[1]
    # Scale and invert the image into binary form (i.e. values are either 0 or 1)
    return 1 - (base_image / 255) if bin_scale else base_image


def convolve_template_xor(
    base: np.ndarray,
    template: np.ndarray,
    error_threshold: float,
    base_error_weight: int,
    template_error_weight: int,
) -> np.ndarray:
    base_h, base_w = base.shape
    template_h, template_w = template.shape

    # Maximum error allowable based on weights
    base_max_error = (
        (template_h * template_w * base_error_weight) + np.sum(template) * (template_error_weight - base_error_weight)
    ) * error_threshold
    # Pre-computed mask to apply weights
    error_weight = (template * (template_error_weight - base_error_weight)) + base_error_weight

    composite = np.zeros(base.shape)
    # Gets all convolution windows efficiently
    base_windows = sliding_window_view(base, template.shape)
    for h in range(base_h - template_h + 1):
        for w in range(base_w - template_w + 1):
            if np.sum(cv2.multiply(cv2.bitwise_xor(base_windows[h][w], template), error_weight)) < base_max_error:
                composite[h : h + template_h, w : w + template_w] = cv2.bitwise_or(
                    composite[h : h + template_h, w : w + template_w], template
                )
    return composite


def process(args: argparse.Namespace):
    config_path = args.config or DEFAULTS.CONFIG_FILE_PATH
    print(f"Using {config_path} as config...")
    with open(config_path, "r") as f:
        config = BaseConfig(**json.load(f))

    base_image = config.base_image
    base_image_prepared = prepare_image(
        base_image.file_path,
        blur_kernel_size=base_image.blur_kernel_size,
        threshold=base_image.threshold,
    )

    print("Preparing templates for processing...")
    templates_prepared = (
        (
            prepare_image(
                template_image.file_path,
                blur_kernel_size=template_image.blur_kernel_size,
                threshold=template_image.threshold,
            ),
            template_image.method,
            template_image.method_parameters,
        )
        for template_image in config.templates
    )

    print("Generating composites...")
    start_time = time()
    composites = Parallel(n_jobs=len(config.templates))(
        delayed(convolve_template_xor)(
            base_image_prepared,
            template_prepared,
            error_threshold=method_parameters.error_threshold,
            base_error_weight=method_parameters.base_error_weight,
            template_error_weight=method_parameters.template_error_weight,
        )
        for template_prepared, _, method_parameters in templates_prepared
    )
    print(f"Completed in {time() - start_time} seconds.")

    print("Merging together composites...")
    output_image = np.zeros(base_image_prepared.shape)
    for composite in composites:
        output_image = cv2.bitwise_or(output_image, composite)
    output_image = (1 - output_image) * 255

    print(f"Writing output image to {config.write_path}")
    cv2.imwrite(config.write_path, output_image)


def get_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", required=False, type=str, help="Path to configuration file")
    return arg_parser.parse_args()


if __name__ == "__main__":
    cmd_args = get_args()
    process(cmd_args)
