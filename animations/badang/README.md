# Badang – animasi cerita rakyat

Animasi kartun (gaya chibi, warna ceria) untuk legenda **Badang**, dengan sarikata
Bahasa Melayu, muzik latar dan kesan bunyi. Video siap ada di
`public/videos/badang.mp4` (1280×720, 24 fps, ±2 min 37 s) dan dipaparkan dalam
catatan blog `src/content/blog/badang.md`.

## Fail

| Fail | Kegunaan |
| --- | --- |
| `index.html` | Seluruh animasi (SVG + JavaScript). Buka dalam pelayar untuk pratonton; `?t=60` lompat ke saat 60. |
| `render.mjs` | Merender setiap bingkai dengan Playwright dan menghantarnya ke ffmpeg. |
| `audio.py` | Menjana muzik latar dan kesan bunyi (numpy sahaja). |
| `badang.ms.srt` | Sarikata untuk dimuat naik ke YouTube. |
| `fonts/` | Fon Fredoka (lesen SIL OFL). |

## Merender semula

```sh
cd animations/badang
node render.mjs meta /tmp/meta.json             # tempoh, isyarat bunyi, sarikata
python3 audio.py /tmp/meta.json /tmp/badang.wav  # runut bunyi
node render.mjs frames /tmp/silent.mp4 24        # video tanpa bunyi
ffmpeg -i /tmp/silent.mp4 -i /tmp/badang.wav -c:v copy -c:a aac -b:a 160k \
  -shortest -movflags +faststart ../../public/videos/badang.mp4
```

Babak ditakrifkan dengan `scene(tempoh, sarikata, lukis, bunyi)` dalam `index.html`;
ubah teks, masa atau watak di situ dan render semula.

## Suara latar

Video ini belum ada suara pencerita. Skrip narasi ialah teks sarikata dalam
`badang.ms.srt` (masa sudah ditetapkan), jadi anda boleh rakam suara sendiri dan
gabungkannya dengan `ffmpeg -i badang.mp4 -i suara.wav -filter_complex amix ...`.
