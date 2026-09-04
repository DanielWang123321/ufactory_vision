# Changelog

## [0.1.0] - 2026-09-04
### Added
- Support Python 3.12 / 3.13 / 3.14: dependencies are segmented by
  `python_version` markers in the requirements files, so a single
  `pip install -r requirements_rs.txt` automatically selects the matching
  versions (legacy locked versions for Python <=3.11, new versions for 3.12-3.14)

### Fixed
- `camera/rs_camera.py`, `camera/depthai_camera.py`: depth image is now
  consistently output as float32
