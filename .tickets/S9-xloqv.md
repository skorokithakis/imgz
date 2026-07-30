---
id: S9-xloqv
status: closed
deps: []
links: []
created: 2026-07-30T19:26:04Z
type: chore
priority: 2
assignee: Stavros Korokithakis
---
# Test that no EXIF is persisted for an uploaded photo

Ready for implementation.

Objective: the existing tests check what Image.strip_exif returns, not what ends up stored. Nothing stops somebody from later passing exif= to the img.save() call in process() and reintroducing a privacy leak with a green suite. Add one test that asserts the stored bytes are clean.

Add a single test to tests/main/test_models.py, next to the other strip_exif tests.

The test should:
- Build a small JPEG in memory that genuinely carries identifying EXIF: Artist, Software, DateTime, an Exif sub-IFD with DateTimeOriginal, and a GPSInfo sub-IFD with latitude and longitude. Use PIL.ExifTags Base, IFD and GPS rather than raw tag numbers. Use obviously fake values, no real names or real coordinates.
- Create the image through ImageFactory with that data, which runs Image.process() via save().
- Assert on the STORED data, that is image.data after processing, and on image.thumbnail_512 as well: the top level EXIF is empty, the GPS and Exif sub-IFDs are empty, and none of the placeholder strings you put in appear anywhere in the raw bytes.

Do not weaken the assertion to only checking getexif(). Searching the raw bytes is the point: it catches metadata that survives in a segment Pillow does not parse back into getexif().

Caveats:
- The default ImageFactory user has no "privacy" feature, so the face detection branch of process() will not run. Keep it that way, this test is not about that path.
- pytest turns warnings into errors (setup.cfg).
- Needs @pytest.mark.django_db, because the factory saves.

Non-goals: do not change main/models.py or any application code, this is a test only. Do not touch the animated GIF path, which deliberately stores the uploaded bytes untouched. Do not add binary fixtures, generate the image in the test.

## Acceptance Criteria

One new test that fails if the exif is passed through to the save() call in process(), and passes as the code stands. Full suite passes.

