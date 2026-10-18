# Home hero ambient background

Used only by the homepage hero (`apps/web/src/components/HomeAmbientBackground.tsx`).

| File | Purpose |
| --- | --- |
| `home-ambient-loop.mp4` | 10.04 s seamless loop, 1280×720, H.264 (yuv420p), 24 fps, no audio track, ~4.1 MB. Final approved render; do not re-encode or replace with an older version. |
| `home-ambient-poster.webp` | Still frame taken from the video at 0.5 s (~99 KB). Shown before the video loads, and instead of the video for reduced motion, data saver, unsupported codecs, load errors and blocked autoplay. The video plays on all screen sizes. |

Playback rules: muted, looped, inline, `preload="metadata"`, `pointer-events: none`, `aria-hidden`.
Paused while the tab is hidden or the hero is out of view; unmounted when leaving the homepage.
The hero fills the first screen (`min-h-[calc(100vh-68px)]`). Only the media layer has an opacity
(`HOME_AMBIENT_OPACITY`); a separate, light `.home-ambient-overlay` in `src/index.css` adds a soft scrim
behind the left text and fades the bottom edge into the next section.

Regression check: `python scripts/test_home_ambient_video_browser.py` (see the script header).
