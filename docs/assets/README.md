# Page assets

Drop-in files the landing page reads. Replace a file (same name) and the page picks it up
with no code changes.

- `profile.jpg` — the circular portrait in the "Why me" section. Square-ish crop works best
  (the page crops to a circle). Until it exists, the page shows an initial as fallback.
- `logos/*.svg` — the brand carousel. The committed files are neutral text wordmarks as
  stand-ins; overwrite each with the official logo (SVG or PNG, keep the filename) for the
  real thing. They render greyscale at ~34px tall, so simple/high-contrast versions work best.
