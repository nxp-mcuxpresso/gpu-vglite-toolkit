### Overview

gpu-vglite-toolkit application allows converting SVG to header only assets.
This graphics assets then can be used with VGLite APIs directly.

This application is implemented in python3 and platform independant.

### Dependency

| Module | URL | License |
| --- | --- | --- |
| svgpathtools | https://github.com/mathandy/svgpathtools | MIT |

### Usage

```bash
./gpu-vglite-toolkit.sh fish.svg > fish.h
```

### Demo with MCUSDK application

clock_freertos application demonstrates generating graphics assets using gpu-vglite-toolkkit.sh

### Known Issues

* At the moment only shape elements are support.
* Font support implementation is ongoing.
* Image support implementation is ongoing.
