# IsolateMusicSymbols
Filters out everything on a music score except certain provided music symbols.

Created for fun, learning, escaping boredom, and mild algorithm designing practice.

## Prerequisites
Python 3 is required.

To set up virtual environment:
```python
pip3 install virtualenv
virtualenv -p python3 venv3
source venv3/bin/activate
```

To install required libraries in virtual environment:
```python
pip3 install -r requirements.txt
```

## Terms
- The _base_ image refers to the music score. It has the accidentals and any other symbols you want to isolate.
- The _template_ image(s) are the **same resolution** cropped image(s) from the *base* image encapsulating a symbol you want to isolate.
- The _error_threshold_ is the proportion of error in the matching between the _template_ and *base* image that is permitted. See [method](#method) for more detail.
- The _base_error_weight_ is the weight placed on pixels where the *base* region does not match the *template* region. See [method](#method) for more detail. Typically smaller than _template_error_weight_.
- The _template_error_weight_ is the weight placed on pixels where the *template* region does not match the *base* region. See [method](#method) for more detail. Typically larger than _base_error_weight_.

## Method
1. Transform *base* and *template* images in binary 2D array representation.
2. Convolve (slide) the smaller *template* images over the *base* image and calculate a statistic:
   1. Perform `xor` (exclusive OR) between the *base* and *template* position. This results in an array that is `1` whenever the images do not match.
   2. From experimentation, it has been found that the *base* region not matching the *template* region is more important than the *template* region not matching the *base* region. Therefore, weight the former higher.
   3. Sum all the values after the transformation. If the `sum < error_threshold`, then imprint the *template* image onto a fresh composite layer.
3. Perform `or` on all composites to obtain the final image.

## Usage

Configuration is provided through a `config.json` file, or anything you name it as. The default configuration file path is `./config.json`.

1. Manual image preparation
   - From the *base* image, **crop out** (*do not screenshot!*) *template* images with at least a 1 pixel white border.
2. Configuration in `config.json`
   - Configure the *base* image processing under the key `config["base_image"]`.
   - Configure the *template* image processing in a list under the key `config["templates"]`.
   - See [configuration fields](#configuration-fields) below on filling the configuration fields.
3. Call `python3 isolate_music_symbols.py [--config <config_path>]`

### Configuration Fields
- `write_path` (str): Path where the output image will be written.
- `base_image` (dict): *Base* image configuration.
  - `file_path` (str): Path to *base* image for reading.
  - `blur_kernel_size` (int, optional): Amount of blur to apply to the *base* image. Must be odd positive integer. Recommended: (1 or 3). Default: 1.
  - `threshold` (int, optional): Threshold used for converting greyscale to black-and-white image. Values below threshold become 0 (black) and values above threshold become 255 (white). Default: 180.
- `templates` (list):
  - (dict):
    - `file_path` (str): Path to *template* image for reading.
    - `blur_kernel_size` (int, optional): Amount of blur to apply to the *template* image. Must be odd positive integer. Recommended: (1 or 3). Default: 1.
    - `threshold` (int, optional): Threshold used for converting greyscale to black-and-white image. Values below threshold become 0 (black) and values above threshold become 255 (white). Default: 180.
    - `method` (str): Default is `"xor_weighted"`. No other method is supported at the moment.
    - `method_parameters` (dict):
      - `error_threshold` (float): See [terms](#terms). Recommended: [0.1, 0.3].
      - `base_error_weight` (int, optional): See [terms](#terms). Recommended: 1. Default: 1.
      - `template_error_weight` (int, optional): See [terms](#terms). Recommended: {2, 3}. Default: 1.

## Example
In the `example` directory, `example/config.json` provides a working example of appropriate configuration values for the *base_image* `example/test_image.png`.

Call `python3 isolate_music_symbols.py --config example/config.json` to try. Open `result.png` when finished to see result.