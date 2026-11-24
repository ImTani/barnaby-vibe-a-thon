"""Barnaby's voice: a Pipecat bot. Browser mic (WebRTC) -> listening layer -> Barnaby's core -> Kokoro -> speaker.

  runtime/voice/.venv/Scripts/python voice/bot.py -t webrtc --port 7860

Layers are picked by env (see .env.example):
  BARNABY_LISTEN = sherpa (Tani's streaming server, default) | whisper (local faster-whisper) | groq (free tier)
  BARNABY_VOICE  = kokoro (local, CPU, British male 'bm_george')
  BARNABY_WAKE   = 1 to require "hey Barnaby" (otherwise push-to-talk in the display gates the mic)
Model files live in models/ inside the repo (nothing goes to ~/.cache).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for _stream in (sys.stdout, sys.stderr):        # Pipecat prints a Unicode banner; Windows redirects default to cp1252
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from loguru import logger  # noqa: E402
from pipecat.pipeline.pipeline import Pipeline  # noqa: E402
from pipecat.pipeline.worker import PipelineParams, PipelineWorker  # noqa: E402
from pipecat.runner.types import RunnerArguments  # noqa: E402
from pipecat.runner.utils import create_transport  # noqa: E402
from pipecat.services.kokoro.tts import KokoroTTSService  # noqa: E402
from pipecat.transcriptions.language import Language  # noqa: E402
from pipecat.transports.base_transport import BaseTransport, TransportParams  # noqa: E402
from pipecat.workers.runner import WorkerRunner  # noqa: E402

from voice.bridge import BarnabyBridge  # noqa: E402
from voice.sherpa_stt import SherpaSTTService  # noqa: E402

MODELS = ROOT / "models"
CORE = os.environ.get("BARNABY_CORE", "http://127.0.0.1:8700")

transport_params = {
    "webrtc": lambda: TransportParams(audio_in_enabled=True, audio_out_enabled=True, audio_in_sample_rate=16000),
}


def make_stt():
    kind = os.environ.get("BARNABY_LISTEN", "sherpa")
    if kind == "whisper":
        from pipecat.audio.vad.silero import SileroVADAnalyzer  # noqa: F401  (segmented STT needs VAD upstream)
        from pipecat.services.whisper.stt import WhisperSTTService
        return WhisperSTTService(model="large-v3-turbo", device=os.environ.get("WHISPER_DEVICE", "cuda"),
                                 download_root=str(MODELS / "whisper"))
    if kind == "groq":
        from pipecat.services.groq.stt import GroqSTTService
        return GroqSTTService(api_key=os.environ["GROQ_API_KEY"])
    return SherpaSTTService(url=os.environ.get("SHERPA_WS_URL", "ws://192.168.1.68:6007"), user_id="june")


def make_tts():
    return KokoroTTSService(
        model_path=str(MODELS / "kokoro" / "kokoro-v1.0.onnx"),
        voices_path=str(MODELS / "kokoro" / "voices-v1.0.bin"),
        settings=KokoroTTSService.Settings(voice=os.environ.get("BARNABY_KOKORO_VOICE", "bm_george"), language=Language.EN_GB),
    )


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    stt, tts = make_stt(), make_tts()
    bridge = BarnabyBridge(core=CORE, require_wake=os.environ.get("BARNABY_WAKE") == "1")
    pipeline = Pipeline([transport.input(), stt, bridge, tts, transport.output()])
    worker = PipelineWorker(pipeline, params=PipelineParams(enable_metrics=False),
                            idle_timeout_secs=runner_args.pipeline_idle_timeout_secs)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("voice client connected")

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        await worker.cancel()

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)
    await runner.run()


async def bot(runner_args: RunnerArguments):
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main
    main()
