#!/usr/bin/env python3
"""Narração com as 4 vozes do LGA Reels Studio, rodando local via onnxruntime.

  faber  masculina, firme e clara   (piper, 22050 Hz, rápida)
  cadu   masculina, jovem e leve    (piper, 22050 Hz, rápida)
  jeff   masculina, grave           (piper, 22050 Hz, rápida)
  dora   feminina, calorosa         (kokoro, 24000 Hz, ~5x mais lenta)

  python3 voice.py <voz> "texto" saida.wav
"""
import os, re, json, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VOZ = os.path.join(HERE, 'voz')
SR_OUT = 48000

VOICES = {
    'faber': dict(engine='piper', sr=22050, noise=.667, noiseW=.8, len=1.0),
    'cadu':  dict(engine='piper', sr=22050, noise=.667, noiseW=.8, len=1.0),
    'jeff':  dict(engine='piper', sr=22050, noise=.667, noiseW=.8, len=1.0),
    'dora':  dict(engine='kokoro', sr=24000),
}

_sess, _pho, _vocab, _style = {}, None, None, {}


def available():
    return [v for v in VOICES if os.path.exists(f'{VOZ}/{v}.onnx')]


def _session(v):
    if v not in _sess:
        import onnxruntime as ort
        o = ort.SessionOptions(); o.intra_op_num_threads = 4
        _sess[v] = ort.InferenceSession(f'{VOZ}/{v}.onnx', o, providers=['CPUExecutionProvider'])
    return _sess[v]


# ----------------------------------------------------------------- normalização PT-BR
SAY = {'QI': 'cê i', 'ENEM': 'enêm', 'IBGE': 'i bê gê é', 'ONU': 'ônu', 'DNA': 'dê êne á',
       'PH': 'pê agá', 'CO2': 'cê ó dois', 'SP': 'São Paulo', 'RJ': 'Rio de Janeiro',
       'EUA': 'Estados Unidos', 'URSS': 'u érre ésse ésse', 'TV': 'tê vê', 'OK': 'ôquei'}
NUM = {'1': 'primeira', '2': 'segunda', '3': 'terceira'}


def norm(t):
    s = ' ' + str(t or '') + ' '
    s = s.replace('___', ' o quê ').replace('_', ' ')
    s = re.sub(r'(\d+)\s?%', r'\1 por cento', s)
    s = re.sub(r'R\$\s?([\d.]+)', lambda m: m.group(1).replace('.', '') + ' reais', s)
    s = re.sub(r'\b([A-ZÀ-Ú]{2,})\b', lambda m: SAY.get(m.group(1), m.group(1).lower()
               if re.search(r'[AEIOUÁÉÍÓÚÂÊÔÃÕ]', m.group(1)) else ' '.join(m.group(1))), s)
    s = re.sub(r'[“”"«»]', '', s)
    s = re.sub(r'[—–]', ', ', s)
    return re.sub(r'\s+', ' ', s).strip()


def _phonemes(text):
    global _pho
    if _pho is None:
        from piper.phonemize_espeak import EspeakPhonemizer
        _pho = EspeakPhonemizer()
    return _pho.phonemize('pt-br', text)


def _trim(a, sr, thr=0.006):
    if not len(a): return a
    loud = np.abs(a) > thr
    if not loud.any(): return a[:0]
    i, j = np.argmax(loud), len(a) - np.argmax(loud[::-1])
    pad = int(sr * .02)
    return a[max(0, i - pad):min(len(a), j + pad)]


def synth(text, voice='faber', speed=1.0, gap=.17, expr=1.0):
    """Returns (float32 mono at 48 kHz, duration in seconds)."""
    import scipy.signal as sg
    v = VOICES[voice]; s = _session(voice); sr = v['sr']
    clean = norm(text)
    if not clean: return np.zeros(0, np.float32), 0.0
    pcs = []
    for sent in _phonemes(clean):
        if v['engine'] == 'piper':
            from piper.phoneme_ids import phonemes_to_ids
            ids = phonemes_to_ids(sent)
            if len(ids) < 3: continue
            r = s.run(None, {'input': np.array([ids], np.int64),
                             'input_lengths': np.array([len(ids)], np.int64),
                             'scales': np.array([v['noise'] * expr, v['len'] / speed, v['noiseW']], np.float32)})
            a = np.asarray(r[0], np.float32).squeeze()
        else:
            global _vocab
            if _vocab is None: _vocab = json.load(open(f'{VOZ}/kokoro_vocab.json'))
            if voice not in _style: _style[voice] = np.fromfile(f'{VOZ}/{voice}.style.f32', np.float32)
            toks = [_vocab[c] for c in ''.join(sent) if c in _vocab][:508]
            if not toks: continue
            st = _style[voice][len(toks) * 256:len(toks) * 256 + 256]
            r = s.run(None, {'tokens': np.array([[0] + toks + [0]], np.int64),
                             'style': st.reshape(1, 256).astype(np.float32),
                             'speed': np.array([speed], np.float32)})
            a = np.asarray(r[0], np.float32).squeeze()
        pcs.append(_trim(a, sr)); pcs.append(np.zeros(int(sr * gap), np.float32))
    if not pcs: return np.zeros(0, np.float32), 0.0
    out = np.concatenate(pcs[:-1])
    out = sg.resample_poly(out, SR_OUT, sr).astype(np.float32)        # to 48 kHz
    m = np.abs(out).max()
    if m > 0: out *= 0.72 / m
    return out, len(out) / SR_OUT


def cache_path(cache_dir, voice, text, speed):
    import hashlib
    k = hashlib.sha1(f'{voice}|{speed}|{text}'.encode()).hexdigest()[:16]
    return os.path.join(cache_dir, f'{voice}_{k}.npy')


def synth_cached(text, voice, cache_dir, speed=1.0):
    os.makedirs(cache_dir, exist_ok=True)
    p = cache_path(cache_dir, voice, text, speed)
    if os.path.exists(p):
        a = np.load(p); return a, len(a) / SR_OUT
    a, d = synth(text, voice, speed)
    np.save(p, a); return a, d


if __name__ == '__main__':
    import sys, soundfile as sf
    a, d = synth(sys.argv[2], sys.argv[1])
    sf.write(sys.argv[3], a, SR_OUT); print(f'{d:.2f} s -> {sys.argv[3]}')
