import os
from typing import List

from pydantic import BaseModel, validator

VALID_METHODS = {"xor_weighted"}


class DEFAULTS:
    BLUR_KERNEL_SIZE = 1
    THRESHOLD = 180
    BASE_ERROR_WEIGHT = 1
    TEMPLATE_ERROR_WEIGHT = 1


class ImagePreparation(BaseModel):
    file_path: str
    blur_kernel_size: int = DEFAULTS.BLUR_KERNEL_SIZE
    threshold: int = DEFAULTS.THRESHOLD

    @validator("file_path", always=True)
    def validate_file_path(cls, file_path: str) -> str:
        if os.path.isfile(file_path):
            return file_path
        raise ValueError(f"Input file {file_path} cannot be found")

    @validator("blur_kernel_size", always=True)
    def validate_blur_kernel_size(cls, blur_kernel_size: int) -> int:
        assert (
            blur_kernel_size > 0 and blur_kernel_size % 2 == 1
        ), "Guassian blur kernel size must be an odd positive number"
        return blur_kernel_size

    @validator("threshold", always=True)
    def validate_threshold(cls, threshold: int) -> int:
        assert threshold >= 0 and threshold <= 255, "Threshold must be between 0 and 255 inclusive"
        return threshold


class ConvolutionSettings(BaseModel):
    error_threshold: float
    base_error_weight: int = DEFAULTS.BASE_ERROR_WEIGHT
    template_error_weight: int = DEFAULTS.TEMPLATE_ERROR_WEIGHT

    @validator("error_threshold", always=True)
    def validate_error_threshold(cls, error_threshold: float) -> float:
        assert error_threshold >= 0 and error_threshold <= 1, "Error threshold must be between 0 and 1 inclusive"
        return error_threshold

    @validator("base_error_weight", always=True)
    def validate_base_error_weight(cls, base_error_weight: int) -> int:
        assert base_error_weight >= 1, "Base error weight must be an integer at least 1"
        return base_error_weight

    @validator("template_error_weight", always=True)
    def validate_template_error_weight(cls, template_error_weight: int) -> int:
        assert template_error_weight >= 1, "Template error weight must be an integer at least 1"
        return template_error_weight


class TemplateConvolution(ImagePreparation):
    method: str
    method_parameters: ConvolutionSettings

    @validator("method", always=True)
    def validate_method(cls, method: str) -> str:
        if method.lower() in VALID_METHODS:
            return method.lower()
        raise ValueError(f"Invalid method: {method}")


class BaseConfig(BaseModel):
    write_path: str
    base_image: ImagePreparation
    templates: List[TemplateConvolution]

    @validator("write_path", always=True)
    def validate_write_path(cls, write_path: str) -> str:
        path_dir = os.path.dirname(os.path.abspath(write_path))
        if os.path.isdir(path_dir) and os.access(path_dir, os.W_OK):
            return write_path
        raise ValueError("Output write path either does not exist or is not writable")
