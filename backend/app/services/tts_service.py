import asyncio
import logging

from backend.app.core.config import settings
from backend.app.core.elevenlabs_client import client


logger = logging.getLogger(__name__)


def generate_audio(text: str):
    """
    Generate audio from text using ElevenLabs.
    Returns an iterable audio stream.
    """

    return client.text_to_speech.convert(
        text=text,
        voice_id=settings.VOICE_ID,
        model_id="eleven_v3",
        output_format="mp3_44100_128"
    )


async def stream_audio(text: str):

    try:

        audio_stream = await asyncio.to_thread(
            generate_audio,
            text
        )

        for chunk in audio_stream:
            yield chunk

    except Exception as e:

        logger.exception(
            f"TTS Error: {e}"
        )

        raise