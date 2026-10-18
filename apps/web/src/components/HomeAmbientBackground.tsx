import React, { useEffect, useRef, useState } from 'react';

/**
 * Home hero ambient background (homepage only).
 *
 * Layers, bottom to top, all inside the hero's `relative overflow-hidden` section:
 *   1. the hero's own dark ink gradient (unchanged)
 *   2. this component's media layer: a static poster, covered by a looping muted <video>
 *      when motion is allowed. Opacity is applied to this media layer only.
 *   3. a separate, light overlay: a soft localized scrim behind the left text block and a
 *      bottom fade into the next section. The video itself stays clearly visible.
 * Everything is pointer-events: none and aria-hidden; content stays fully opaque above it.
 *
 * The video is a plain HTMLVideoElement (no WebGL). It is only rendered on the home page,
 * paused when the tab is hidden or the hero is scrolled out of view, and replaced by the
 * poster for reduced motion, data saver, unsupported codecs or load errors. A refused autoplay
 * (NotAllowedError) keeps the video and retries on the first pointerdown/keydown.
 * It plays on every screen size (muted + playsInline, so mobile autoplay is allowed).
 */

export const HOME_AMBIENT_VIDEO_SRC = '/assets/home/home-ambient-loop.mp4';
export const HOME_AMBIENT_POSTER_SRC = '/assets/home/home-ambient-poster.webp';
/** Opacity of the media layer (video / poster) only. Tuned from real screenshots. */
export const HOME_AMBIENT_OPACITY = 0.8;

const REDUCED_MOTION_QUERY = '(prefers-reduced-motion: reduce)';

type PosterReason = 'reduced-motion' | 'save-data' | 'unsupported' | 'error';

const matches = (query: string): boolean =>
  typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia(query).matches;

const prefersSaveData = (): boolean => {
  if (typeof navigator === 'undefined') return false;
  const connection = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
  return Boolean(connection?.saveData);
};

const canPlayMp4 = (): boolean => {
  if (typeof document === 'undefined') return false;
  const probe = document.createElement('video');
  return typeof probe.canPlayType === 'function' && probe.canPlayType('video/mp4; codecs="avc1.4D401F"') !== '';
};

/** Re-evaluates a media query on change so the layer follows OS / viewport changes live. */
const useMediaQuery = (query: string): boolean => {
  const [value, setValue] = useState(() => matches(query));
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const mql = window.matchMedia(query);
    const onChange = () => setValue(mql.matches);
    onChange();
    mql.addEventListener?.('change', onChange);
    return () => mql.removeEventListener?.('change', onChange);
  }, [query]);
  return value;
};

export const HomeAmbientBackground: React.FC = () => {
  const reducedMotion = useMediaQuery(REDUCED_MOTION_QUERY);
  const [saveData] = useState(prefersSaveData);
  const [mp4Supported] = useState(canPlayMp4);
  const [failure, setFailure] = useState<PosterReason | null>(null);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const posterReason: PosterReason | null = reducedMotion
    ? 'reduced-motion'
    : saveData
      ? 'save-data'
      : !mp4Supported
        ? 'unsupported'
        : failure;
  const showVideo = posterReason === null;

  useEffect(() => {
    if (!showVideo) return;
    const video = videoRef.current;
    const root = rootRef.current;
    if (!video || !root) return;

    let inView = true;
    let disposed = false;
    let waitingForGesture = false;

    const sync = () => {
      if (disposed) return;
      const shouldPlay = inView && document.visibilityState === 'visible';
      if (!shouldPlay) {
        if (!video.paused) video.pause();
        return;
      }
      if (!video.paused) return;
      // Muted is required for autoplay; set the property explicitly (React does not always reflect the attribute).
      video.muted = true;
      const attempt = video.play();
      if (attempt && typeof attempt.catch === 'function') {
        attempt.then(() => { waitingForGesture = false; }).catch((error: DOMException) => {
          if (disposed) return;
          const name = error?.name;
          // AbortError: a pause()/load raced the play(). NotAllowedError: autoplay was refused;
          // keep the video (its poster frame stays visible) and retry on the first user gesture.
          if (name === 'AbortError') return;
          if (name === 'NotAllowedError') { waitingForGesture = true; return; }
          setFailure('error');
        });
      }
    };

    const onGesture = () => {
      if (waitingForGesture) sync();
    };

    let observer: IntersectionObserver | null = null;
    if (typeof IntersectionObserver === 'function') {
      observer = new IntersectionObserver(entries => {
        inView = entries.some(entry => entry.isIntersecting);
        sync();
      }, { threshold: 0 });
      observer.observe(root);
    }
    document.addEventListener('visibilitychange', sync);
    // (Re)try as soon as the media has data; covers slow loads and elements that were paused early.
    video.addEventListener('loadeddata', sync);
    video.addEventListener('canplay', sync);
    window.addEventListener('pointerdown', onGesture, { passive: true });
    window.addEventListener('keydown', onGesture);
    sync();

    return () => {
      // Only pause. Never strip the source here: in React StrictMode (dev) this cleanup runs and the
      // effect re-runs on the SAME mounted <video>. React removes the element on real unmount, which
      // also releases the decoder and the network connection.
      disposed = true;
      observer?.disconnect();
      document.removeEventListener('visibilitychange', sync);
      video.removeEventListener('loadeddata', sync);
      video.removeEventListener('canplay', sync);
      window.removeEventListener('pointerdown', onGesture);
      window.removeEventListener('keydown', onGesture);
      video.pause();
    };
  }, [showVideo]);

  const handleError = () => setFailure('error');

  return (
    <div
      ref={rootRef}
      aria-hidden="true"
      data-testid="home-ambient-bg"
      data-ambient-mode={showVideo ? 'video' : 'poster'}
      data-ambient-reason={posterReason ?? 'playing'}
      className="home-ambient absolute inset-0 pointer-events-none select-none overflow-hidden"
    >
      <div className="home-ambient-media absolute inset-0" style={{ opacity: HOME_AMBIENT_OPACITY }}>
        <div
          className="home-ambient-frame absolute inset-0 bg-cover"
          style={{ backgroundImage: `url('${HOME_AMBIENT_POSTER_SRC}')` }}
        />
        {showVideo && (
          <video
            ref={videoRef}
            className="home-ambient-frame absolute inset-0 w-full h-full object-cover"
            autoPlay
            muted
            loop
            playsInline
            preload="metadata"
            poster={HOME_AMBIENT_POSTER_SRC}
            disablePictureInPicture
            disableRemotePlayback
            tabIndex={-1}
            onError={handleError}
          >
            <source src={HOME_AMBIENT_VIDEO_SRC} type="video/mp4" onError={handleError} />
          </video>
        )}
      </div>
      <div className="home-ambient-overlay absolute inset-0" />
    </div>
  );
};

export default HomeAmbientBackground;
