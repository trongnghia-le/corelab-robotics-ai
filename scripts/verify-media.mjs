/** Optional online maintenance check; normal builds/tests never need Internet. */
import { readFileSync } from "node:fs";
const { videos } = JSON.parse(
  readFileSync(
    new URL("../content/media/videos.v1.json", import.meta.url),
    "utf8",
  ),
);
let failures = 0;
for (const video of videos) {
  try {
    const source = await fetch(video.sourceUrl, {
      signal: AbortSignal.timeout(20000),
    });
    if (!source.ok) throw new Error(`source HTTP ${source.status}`);
    const sourceText = await source.text();
    const id =
      video.youtubeId ??
      new URL(source.url).searchParams.get("v") ??
      sourceText.match(
        /youtube(?:-nocookie)?\.com\/(?:embed\/|watch\?v=)([\w-]{11})/,
      )?.[1];
    if (id) {
      const result = await fetch(
        `https://www.youtube.com/oembed?url=${encodeURIComponent(`https://www.youtube.com/watch?v=${id}`)}&format=json`,
        { signal: AbortSignal.timeout(20000) },
      );
      if (!result.ok) throw new Error(`oEmbed HTTP ${result.status}`);
      const data = await result.json();
      if (
        data.author_name !== video.verifiedChannel ||
        data.title !== video.verifiedTitle
      )
        throw new Error(
          "title/channel changed; review before updating verification evidence",
        );
    }
    console.log(`OK ${video.id}`);
  } catch (error) {
    failures++;
    console.error(`REVIEW ${video.id}: ${error.message}`);
  }
}
if (failures) process.exitCode = 1;
