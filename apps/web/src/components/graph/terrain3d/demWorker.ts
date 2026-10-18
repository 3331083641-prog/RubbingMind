/**
 * DEM decode worker: Terrarium PNG -> Float32 metres.
 * Kept off the main thread so panning stays smooth while tiles stream in.
 */
interface DecodeRequest {
  id: number;
  buffer: ArrayBuffer;
}

const SIZE = 256;

function decode(data: Uint8ClampedArray, width: number, height: number): Float32Array {
  const heights = new Float32Array(width * height);
  for (let i = 0, p = 0; i < heights.length; i++, p += 4) {
    heights[i] = data[p] * 256 + data[p + 1] + data[p + 2] / 256 - 32768;
  }
  return heights;
}

self.onmessage = async (event: MessageEvent<DecodeRequest>) => {
  const { id, buffer } = event.data;
  try {
    const bitmap = await createImageBitmap(new Blob([buffer], { type: 'image/png' }));
    const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
    const context = canvas.getContext('2d', { willReadFrequently: true });
    if (!context) throw new Error('no 2d context');
    context.drawImage(bitmap, 0, 0);
    const image = context.getImageData(0, 0, SIZE, SIZE);
    const heights = decode(image.data, SIZE, SIZE);
    bitmap.close();
    (self as unknown as Worker).postMessage({ id, heights }, [heights.buffer]);
  } catch (error) {
    (self as unknown as Worker).postMessage({ id, error: String(error) });
  }
};
