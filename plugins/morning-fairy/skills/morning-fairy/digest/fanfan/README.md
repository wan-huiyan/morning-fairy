# fanfan icons, bundled for the morning brief

Copied from **TangfanOVO/fanfan-icons** at commit `5ecb58513b66f9dd801fb2542d588ebd96f9f9b5`
(<https://github.com/TangfanOVO/fanfan-icons>), MIT licence, by 唐幡. The licence is in `LICENSE` beside this file.

What is here, and where each part came from in that repo:

- `thin/`, `thick/`, `thin-highlight/`, `thick-highlight/`: the motion icons, from `motion/svg/<style>/`.
  Four animals (cat, dog, lop, bunny) and only the nouns the brief uses: sun bell ticket robot trophy clock news
  mail search file sparkles palette moon music wand sleep star face-whole alarm heart.
- `favicon/<style>/` and `favicon/<line>-sleep/`: the still `face-whole` drawings, from `svg/<style>/` and
  `svg/thin-sleep/`, `svg/thick-sleep/` (the repo has no sleeping "highlight" set: closed eyes have no shine).
  Used only for the browser-tab icon.
- `fanfan-motion.css`, `fanfan-motion.js`: unchanged, from `motion/`. Their MIT header stays on top when the
  builder copies them into a page.
- `motion.json`: unchanged, from `motion/`. The builder reads which icons have their own trick from it.

`build_digest.py` reads these files when a `look.json` asks for fanfan icons, and `serve.py` serves the motion
icons at `/fanfan/<style>/<animal>-<noun>.svg` for the picker's previews. Nothing here is fetched from the network.
To refresh, copy the same paths again from a newer commit and update the commit above.
