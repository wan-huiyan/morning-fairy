# Third-party notices

morning-fairy itself is MIT licensed (see [LICENSE](LICENSE)). It also uses the following.

## fanfan icons (bundled)

The little animal icons in `plugins/morning-fairy/skills/morning-fairy/digest/fanfan/` come from
[TangfanOVO/fanfan-icons](https://github.com/TangfanOVO/fanfan-icons) at commit
`5ecb58513b66f9dd801fb2542d588ebd96f9f9b5`. That folder's `README.md` lists exactly which files were copied.

```
MIT License

Copyright (c) 2026 唐幡 (fanfan 图标 Fanfan Icons)

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

The same notice is in `digest/fanfan/LICENSE`, and the builder keeps fanfan's own MIT header on the motion
CSS and script it copies into a page.

## Clawd stickers (loaded from the artist, plus two screenshots)

If you pick Clawd as your mascot, the page shows stickers by alwinecor from
[alwinecor/clawd-stickers](https://github.com/alwinecor/clawd-stickers), licensed
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

- **The code bundles no Clawd file.** Your browser loads each sticker as a picture from the artist's
  repository through jsDelivr, pinned to commit `516f40536c9e3aaaa9995c267daad6e4d45e3d80`, when the page opens.
- The page credits the artist wherever Clawd appears.
- Clawd is a character that belongs to Anthropic. These stickers are unofficial fan art, and their licence
  allows non-commercial use only. Whether your own use fits that licence is your call.
- **Two screenshots show one sticker.** `docs/picker.png` and `docs/picker-phone.png` picture the picker with
  `dev-life/theme/clawd-dev-life/assets/idle.svg` (same commit) on its Clawd card. Because they contain the
  artist's work, these two images are licensed
  [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), not MIT: credit alwinecor, no commercial
  use, and share any adaptation under the same licence. The rest of the repository stays MIT.
