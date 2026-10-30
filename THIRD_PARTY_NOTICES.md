# Third-party notices and acknowledgments

CoreLab's licenses cover its original work only. Third-party libraries, icons, names and external learning materials retain their own licenses and copyright notices. Links identify their creators; they do not imply ownership, redistribution permission or endorsement.

## Educational references

The source release distributes links and original CoreLab explanations, not copies of external books, lectures, videos, slides, thumbnails or photographs. Creator/source attribution remains in lesson `source_refs`, [the video registry](content/media/videos.v1.json), [the reference list](reference/LEARNING_SOURCES.md) and the application reference catalog.

Resources include 3Blue1Brown / Grant Sanderson; MIT OpenCourseWare and Gilbert Strang; Modern Robotics / Kevin M. Lynch and Frank C. Park; MIT Underactuated Robotics / Russ Tedrake; Stanford CS231n; David Silver / Google DeepMind; Enthought / Alexandre Chabot-Leclerc; CppCon / Ben Saks; Python and NumPy documentation; LearnCpp; Dive into Deep Learning; ROS 2; MuJoCo; Szeliski; Sutton and Barto; Berkeley Deep RL; CleanRL; LeRobot; and CLVR publications.

**The external works' redistribution rights have not been granted to CoreLab.** Their terms differ and are not converted to CC BY 4.0 by inclusion in a reference list. Check the particular work and its rights holder before copying or adapting it. Availability checks on video URLs are not license clearance. No external material with unverified redistribution rights is included as a downloaded media/book asset in this release.

## Software dependencies

Dependencies are installed through npm and are not vendored in the Git source tree. `package-lock.json` records exact package versions and available license metadata. Keep the corresponding installed `LICENSE`, `COPYING` and `NOTICE` files when redistributing dependency code or build artifacts.

| Direct dependency                                     | Declared license                                     |
| ----------------------------------------------------- | ---------------------------------------------------- |
| Next.js; React; React DOM                             | MIT                                                  |
| Tailwind CSS; `@tailwindcss/postcss`                  | MIT                                                  |
| React Flow (`@xyflow/react`)                          | MIT                                                  |
| gray-matter; Zod                                      | MIT                                                  |
| react-markdown; remark-gfm; remark-math; rehype-katex | MIT                                                  |
| KaTeX                                                 | MIT                                                  |
| Lucide React                                          | ISC, with Feather-derived portions identified as MIT |

This table is not a complete notice bundle for a prebuilt distribution. Transitive packages have separate terms, including MPL-2.0 (Lightning CSS), LGPL-3.0-or-later (optional Sharp/libvips platform packages), and CC BY 4.0 (caniuse-lite data). CoreLab does not relicense these components. A future binary, container or packaged build must retain the notices and satisfy the applicable source/redistribution obligations of everything it includes. This release publishes source, not a bundled executable.

The real screenshots in `docs/images/` contain the application's interface and locally rendered original diagrams, including Lucide icons. They contain no external video frames or lecture slides. Original screenshot portions follow [LICENSING.md](LICENSING.md); third-party artwork keeps its original terms.

## Lucide notice

The following notice is retained verbatim from `lucide-react` 0.468.0:

```text
ISC License

Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```

Lucide's notice explicitly credits its Feather-derived MIT portions. Preserve that credit as well as the applicable MIT permission notice when redistributing those portions.

## KaTeX notice

The following notice is retained verbatim from the installed KaTeX package, whose CSS/fonts render lesson mathematics locally:

```text
The MIT License (MIT)

Copyright (c) 2013-2020 Khan Academy and other contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Upstream license texts and other package notices remain authoritative. Do not remove notices from installed dependencies when producing a distributable build.
