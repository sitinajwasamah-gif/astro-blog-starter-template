"""Synthesises the soundtrack for the Badang animation (numpy only).

Usage: python3 audio.py meta.json out.wav
meta.json comes from `node render.mjs meta meta.json` and supplies the
total duration and the list of [time, sfx-name] cues.
"""
import json
import sys
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, attack=0.005, decay=0.3):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / decay)


def lowpass(x, cutoff):
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(spec, len(x))


def bandpass(x, lo, hi):
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= ((f > lo) & (f < hi)).astype(float)
    return np.fft.irfft(spec, len(x))


def glide(f0, f1, dur, shape='sin'):
    t = t_axis(dur)
    f = np.geomspace(f0, f1, len(t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) if shape == 'sin' else np.sign(np.sin(ph)) * 0.5


def noise(dur):
    return rng.uniform(-1, 1, int(dur * SR))


def mallet(freq, dur=0.6, bright=0.35):
    """Gamelan/marimba-like struck tone."""
    t = t_axis(dur)
    tone = np.sin(2 * np.pi * freq * t) + bright * np.sin(2 * np.pi * freq * 4.0 * t) * np.exp(-t / 0.05)
    tone += 0.25 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.12)
    return tone * env(len(t), 0.003, dur / 3)


def bell(freq, dur=1.2):
    t = t_axis(dur)
    tone = sum(a * np.sin(2 * np.pi * freq * m * t) for m, a in [(1, 1), (2.0, .5), (3.01, .3), (4.2, .2)])
    return tone * env(len(t), 0.002, dur / 3) * 0.5


def place(buf, clip, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(clip))
    buf[i:j] += clip[: j - i] * gain


# --- Sound effects ---------------------------------------------------------
def sfx(name):
    if name == 'pop':
        return glide(900, 380, 0.09) * env(int(.09 * SR), .002, .04)
    if name == 'chime':
        out = np.zeros(int(1.6 * SR))
        for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
            place(out, bell(f, 1.2), k * 0.09)
        return out * 0.6
    if name == 'boing':
        t = t_axis(0.5)
        f = 220 + 260 * t / .5 + 60 * np.sin(2 * np.pi * 14 * t)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), .005, .2)
    if name == 'chop':
        n = lowpass(noise(0.12), 2500) * env(int(.12 * SR), .001, .03)
        return 1.6 * n + 0.6 * glide(160, 70, .12) * env(int(.12 * SR), .001, .05)
    if name == 'step':
        return glide(120, 60, .15) * env(int(.15 * SR), .002, .05) * 0.5
    if name in ('splash', 'bigsplash'):
        d = 0.7 if name == 'splash' else 1.6
        x = bandpass(noise(d), 300, 5000) * env(int(d * SR), .01, d / 4)
        if name == 'bigsplash':
            x += 0.8 * glide(90, 40, d) * env(int(d * SR), .005, .3)
        return x * 0.9
    if name == 'clack':
        return bandpass(noise(.05), 1500, 6000) * env(int(.05 * SR), .001, .01) * 1.5
    if name == 'whoosh':
        d = 0.5
        t = t_axis(d)
        return bandpass(noise(d), 400, 3000) * np.sin(np.pi * t / d) ** 2 * 0.9
    if name == 'munch':
        out = np.zeros(int(.4 * SR))
        for k in range(3):
            place(out, lowpass(noise(.07), 1800) * env(int(.07 * SR), .002, .02), k * .12)
        return out * 1.4
    if name == 'grab':
        out = glide(200, 90, .15) * env(int(.15 * SR), .002, .06)
        place(out, glide(1200, 2000, .12) * env(int(.12 * SR), .002, .06), 0, 0.5)
        return out
    if name == 'squeak':
        t = t_axis(.35)
        f = 1400 + 500 * np.sin(2 * np.pi * 6 * t)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), .01, .15) * 0.35
    if name == 'blurp':
        t = t_axis(.6)
        f = 140 + 60 * np.sin(2 * np.pi * 9 * t)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), .01, .25) * 0.9
    if name == 'yuck':
        return glide(500, 180, .5, 'sq') * env(int(.5 * SR), .02, .3) * 0.35
    if name == 'gulp':
        return glide(320, 120, .18) * env(int(.18 * SR), .005, .08)
    if name == 'magic':
        out = np.zeros(int(2.2 * SR))
        for k, f in enumerate([523.3, 659.3, 784, 1046.5, 1318.5, 1568, 2093]):
            place(out, bell(f, 1.0), k * 0.08)
        out += bandpass(noise(2.2), 6000, 12000) * env(len(out), .3, .6) * 0.15
        return out * 0.6
    if name == 'rumble':
        return lowpass(noise(1.2), 150) * env(int(1.2 * SR), .2, .5) * 4
    if name == 'ding':
        return bell(1760, 1.4)
    if name == 'cheer':
        d = 2.2
        out = bandpass(noise(d), 500, 3500) * env(int(d * SR), .15, .8) * 0.5
        for k in range(14):
            f0 = rng.uniform(300, 650)
            place(out, glide(f0, f0 * 1.4, .35, 'sq') * env(int(.35 * SR), .03, .15) * 0.08, rng.uniform(0, 1))
        return out
    if name == 'wave':
        d = 3.0
        t = t_axis(d)
        return lowpass(noise(d), 900) * np.sin(np.pi * t / d) * 0.8
    if name == 'drum':
        out = np.zeros(int(1.4 * SR))
        for k, at in enumerate([0, .25, .5, .62, .75]):
            place(out, glide(150 if k < 3 else 110, 60, .3) * env(int(.3 * SR), .002, .12), at)
        return out
    if name == 'strain':
        d = 1.8
        t = t_axis(d)
        f = 110 + 8 * np.sin(2 * np.pi * 7 * t)
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
        return lowpass(x, 700) * np.sin(np.pi * t / d) * 0.25
    if name == 'thud':
        out = glide(80, 35, .6) * env(int(.6 * SR), .002, .25) * 1.4
        place(out, lowpass(noise(.3), 400) * env(int(.3 * SR), .002, .08), 0, 2)
        return out
    if name == 'gasp':
        d = .4
        t = t_axis(d)
        return bandpass(noise(d), 800, 4000) * np.sin(np.pi * t / d) * 0.5
    raise ValueError(name)


# --- Background music ------------------------------------------------------
def music(total, moods):
    out = np.zeros(int((total + 2) * SR))
    bpm = 104
    beat = 60 / bpm
    major = [261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33, 659.25]
    minor = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33]
    prog_major = [130.81, 110.0, 87.31, 98.0]  # C Am F G
    prog_minor = [110.0, 87.31, 98.0, 82.41]   # Am F G E
    note = 0
    n_beats = int(total / beat)
    for b in range(n_beats):
        at = b * beat
        mood = next(m for a, z, m in moods if a <= at < z)
        bar = (b // 4) % 4
        if mood == 'night':
            if b % 2 == 0:
                place(out, mallet(prog_minor[bar], 1.4, 0.1), at, 0.22)
            if b % 2 == 1:
                place(out, mallet(minor[(b * 3) % 6 + 1], 1.2, 0.2), at, 0.10)
            continue
        scale = major
        # bass + soft chord pulse
        if b % 2 == 0:
            place(out, mallet(prog_major[bar], 0.9, 0.1), at, 0.26)
        place(out, mallet(prog_major[bar] * 2, 0.35, 0.05), at + beat / 2, 0.08)
        # melody: seeded pentatonic random walk in eighth notes
        for h in range(2):
            if rnd_melody[(b * 2 + h) % len(rnd_melody)] < 0.3:
                continue
            note = int(np.clip(note + rng.integers(-2, 3), 0, len(scale) - 1))
            place(out, mallet(scale[note] * (2 if mood == 'tense' else 1), 0.5, 0.4), at + h * beat / 2, 0.13)
        # light shaker / kendang
        place(out, bandpass(noise(.05), 5000, 11000) * env(int(.05 * SR), .001, .015), at + beat / 2, 0.12)
        if mood == 'tense' or b % 4 == 0:
            place(out, glide(140, 70, .2) * env(int(.2 * SR), .002, .08), at, 0.35 if mood == 'tense' else 0.2)
    return out


rnd_melody = rng.uniform(0, 1, 64)


def main():
    meta = json.load(open(sys.argv[1]))
    total = meta['total']
    # Musical mood per time range (seconds) — mirrors the scene list.
    moods = [(0, 34, 'day'), (34, 69, 'night'), (69, 112, 'day'), (112, 133, 'tense'), (133, total + 5, 'day')]
    mix = music(total, moods) * 0.8
    sfx_bus = np.zeros_like(mix)
    cache = {}
    for at, name in meta['sfx']:
        if name not in cache:
            cache[name] = sfx(name)
        place(sfx_bus, cache[name], at, 0.7)
    mix = mix + sfx_bus
    mix = mix[: int(total * SR)]
    # fade in/out and normalise
    fade = int(1.5 * SR)
    mix[:int(.5 * SR)] *= np.linspace(0, 1, int(.5 * SR))
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.3) * 0.85
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(sys.argv[2], 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == '__main__':
    main()
