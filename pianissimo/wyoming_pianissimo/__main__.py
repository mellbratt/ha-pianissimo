"""Entry point: python -m wyoming_pianissimo --uri tcp://0.0.0.0:10300"""

import argparse
import asyncio
import logging
import os
from functools import partial

import onnx_asr
from wyoming.info import AsrModel, AsrProgram, Attribution, Info
from wyoming.server import AsyncServer

from . import __version__
from .handler import PianissimoEventHandler

_LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = "KlangAI/pianissimo-sv-onnx"
QUANTIZATIONS = ["int8", "int4", "fp16", "fp32"]


def _env(name: str, default: str) -> str:
    return os.environ.get(f"WYO_PIANISSIMO_{name}") or default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uri", default=_env("URI", "tcp://0.0.0.0:10300"))
    parser.add_argument(
        "--model",
        default=_env("MODEL", DEFAULT_MODEL),
        help="Hugging Face repo id or local directory with the ONNX export",
    )
    parser.add_argument(
        "--quantization",
        default=_env("QUANTIZATION", "int8"),
        choices=QUANTIZATIONS,
    )
    parser.add_argument(
        "--data-dir",
        default=_env("DATA_DIR", ""),
        help="Cache directory for downloaded models (sets HF_HOME)",
    )
    parser.add_argument(
        "--pad-seconds",
        type=float,
        default=float(_env("PAD_SECONDS", "0.5")),
        help="Silence added before and after the audio (prevents a dropped first word)",
    )
    parser.add_argument("--debug", action="store_true", default=_env("DEBUG", "") in ("1", "true"))
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.data_dir:
        os.environ.setdefault("HF_HOME", args.data_dir)

    _LOGGER.info("Loading %s (%s)", args.model, args.quantization)
    quant = None if args.quantization == "fp32" else args.quantization
    model = onnx_asr.load_model(args.model, quantization=quant)
    _LOGGER.info("Model loaded")

    attribution = Attribution(name="Klang AI", url="https://huggingface.co/KlangAI/pianissimo-sv")
    info = Info(
        asr=[
            AsrProgram(
                name="pianissimo",
                description="Klang Pianissimo – Swedish speech recognition (Parakeet v3 fine-tune)",
                attribution=attribution,
                installed=True,
                version=__version__,
                models=[
                    AsrModel(
                        name=f"pianissimo-sv-{args.quantization}",
                        description="Klang Pianissimo, Swedish",
                        attribution=attribution,
                        installed=True,
                        version=None,
                        languages=["sv"],
                    )
                ],
            )
        ],
    )

    server = AsyncServer.from_uri(args.uri)
    _LOGGER.info("Listening on %s", args.uri)
    model_lock = asyncio.Lock()
    await server.run(partial(PianissimoEventHandler, info, model, model_lock, args.pad_seconds))


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
