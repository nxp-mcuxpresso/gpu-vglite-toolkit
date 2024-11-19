### Overview

gpu-vglite-toolkit application allows converting SVG to header only assets.
This graphics assets then can be used with VGLite APIs directly.

This application is implemented in python3 and platform independent.

### Dependency

| Module | URL | License |
| --- | --- | --- |
| svgpathtools | https://github.com/mathandy/svgpathtools | MIT |

### NOTE

1. On 1st run of gpu-vglite-toolkit.sh it clones svgpathtools with NXP fixes and due to git fetch it can take some time.
2. When in DEVELOPEMNT use internal URL
3. Ensure PYTHONPATH contains svgpathtools with NXP fixes
   e.g. export PYTHONPATH=$PYTHONPATH:/opt/nxp/gpu-vglite-toolkit/svgpathtools

### Usage

```bash
./gpu-vglite-toolkit.sh tests/paint-color-01-t.svg.svg > paint_color_01_t.h
```

### Tests

There are some tests vectors presents in 'tests' folder.
[SVGT12 conformance suite](https://www.w3.org/Graphics/SVG/Test/20080912/W3C_SVG_12_TinyTestSuite.tar.gz) contains conformance test vectors. Out of which 'shape' related vectors has been validated with gpu-vglite-toolkit.


### Demo with MCUSDK application

clock_freertos application demonstrates generating graphics assets using gpu-vglite-toolkkit.sh

### Known Issues

* At the moment only shape elements are support.
* Font support implementation is ongoing.
* Image support implementation is ongoing.
* Opacity is not supported
* font support will be available by Dec 2024
* image support will be available by Dec 2024
* Fallback paint color feature will be available by Dec 2024