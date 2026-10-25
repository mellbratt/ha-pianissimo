# Pianissimo

Local Swedish speech-to-text for Assist using Klang Pianissimo (CC BY 4.0).

After starting the add-on, configure the discovered Wyoming integration, then select **pianissimo** as speech-to-text in your voice assistant and set the language to Svenska.

The model (about 660 MB for int8) is downloaded on first start and cached in the add-on's data folder.

## Options

- `quantization`: `int8` (default), `int4`, `fp16` or `fp32`.
- `pad_seconds`: silence added around the audio; prevents a dropped first word. Default 0.5.
- `debug_logging`: verbose logs.
