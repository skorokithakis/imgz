---
id: S9-mevee
status: open
deps: []
links: []
created: 2026-07-30T18:46:46Z
type: bug
priority: 1
assignee: Stavros Korokithakis
---
# Auto-orient uploaded images and stop corrupting palette images

Ready for implementation.

Two defects in Image.strip_exif in main/models.py.

1. Uploaded photos are stored sideways. The docstring says the method auto-orients the image, but it never did. process() then saves with img.save(outp, format=self.format), passing no exif, so the EXIF orientation tag is discarded. A phone photo with Orientation=6 is therefore stored rotated, with nothing left for a viewer to correct. This matters more now that the upload page has a camera button.

2. Palette images are corrupted. strip_exif builds a blank PILImage.new(image.mode, image.size) and copies pixels into it. For mode "P" that produces an image with the default palette rather than the source palette, so the colours come out wrong. The previous putdata(getdata()) implementation had the same defect, so this is old, not a regression.

Changes:
- Apply the EXIF orientation with PIL.ImageOps.exif_transpose before stripping. Note it returns a new image and leaves the input untouched, which is what we want, since process() reuses img afterwards.
- Strip the metadata in a way that preserves the palette. Copying the image and then clearing the "info" dict keeps mode, palette and alpha intact, unlike building a blank image and pasting into it. Whatever you choose, the result must carry no EXIF and must round-trip a "P" mode image without colour change.
- Make sure the docstring matches what the code actually does when you are finished.

Tests, in tests/main/test_models.py, alongside the existing test_strip_exif_removes_exif:
- An image with EXIF Orientation=6 comes out rotated, and its stored dimensions are swapped.
- A "P" mode image keeps its colours through strip_exif. Compare converted RGB pixel values, not palette internals.
Keep both tests compact and generate the images in the test. Do not add binary fixtures.

Caveats:
- Animated GIFs never reach strip_exif (process() skips them), so do not try to handle multi-frame images.
- pytest turns warnings into errors (setup.cfg filterwarnings = error), so a deprecated Pillow call will fail the suite.

Non-goals: do not change how process() saves the image, do not preserve any other metadata such as ICC profiles, do not touch the thumbnail or face-detection paths.

## Acceptance Criteria

strip_exif applies the EXIF orientation and returns an image with no EXIF, and a palette image survives it with unchanged colours. New tests cover both, and the full suite passes.

