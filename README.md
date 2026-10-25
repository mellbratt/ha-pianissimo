# ha-pianissimo

Home Assistant add-on that runs [Klang Pianissimo](https://huggingface.co/KlangAI/pianissimo-sv), an open Swedish speech-recognition model, as local speech-to-text for Assist. It runs on the same machine as Home Assistant (Raspberry Pi or x86) and talks to Home Assistant over the Wyoming protocol, the same way the official Whisper add-on does.

## Install

1. Settings → Add-ons → Add-on Store → ⋮ → Repositories → add `https://github.com/mellbratt/ha-pianissimo`.
2. Install **Pianissimo (Swedish speech-to-text)** and start it. The first install builds the image on the device; the first start downloads the model (about 660 MB for int8) into the add-on's data folder.
3. Settings → Devices & services: the Wyoming integration should appear as discovered. Configure it.
4. Settings → Voice assistants → your assistant → Speech-to-text: **pianissimo**, language Svenska.

## Requirements

| | |
|---|---|
| Architecture | aarch64 (Raspberry Pi 4/5 with 64-bit HA OS) or amd64 |
| RAM | ~1.4 GB peak for the int8 model (measured on x86). A Pi with 2 GB is likely too small next to HA itself; 4 GB or more is recommended. |
| Disk | ~660 MB (int8), ~1.3 GB (fp16) |

## Options

| Option | Default | |
|---|---|---|
| `quantization` | `int8` | `int8`, `int4`, `fp16` or `fp32`. int8 is the smallest that has been tested. |
| `pad_seconds` | `0.5` | Silence added before and after the audio. Without it the model dropped the first word in testing ("Tänd lampan…" → "lampan…"). |
| `debug_logging` | `false` | |

## Measured so far

Tested on a 2-core x86 VM with synthetic Swedish speech (Piper `sv_SE-nst-medium`), int8:

| Command | Transcript | Time after end of speech |
|---|---|---|
| Tänd lampan i vardagsrummet. | Tänd lampan i vagsrummet. | 0.78 s |
| Sätt temperaturen i sovrummet till tjugoen grader. | Sätt temperaturen i sovrummet till 21 grader. | 0.91 s |
| Släck alla lampor på övervåningen och starta en timer på tio minuter. | Släck alla lampor på övervåningen och sta en timmer på 10 minuter. | 0.96 s |

The errors may come from the synthetic voice rather than the model. **Not yet measured on a Raspberry Pi** – expect slower times there.

## Testing without Home Assistant

```sh
pip install "onnx-asr[cpu,hub]" wyoming numpy
cd pianissimo && python3 -m wyoming_pianissimo --uri tcp://127.0.0.1:10300
python3 script/transcribe_wav.py command.wav   # in another shell
```

## Licences

Code: MIT. Model: CC BY 4.0, © Klang AI – downloaded at runtime from Hugging Face, not redistributed here.
