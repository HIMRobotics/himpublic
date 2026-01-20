#!/usr/bin/env python3
"""
ElevenLabs Streaming TTS - Real-time text-to-speech using WebSocket API.

Uses the eleven_flash_v2_5 model for lowest latency.

Usage:
    from elevenlabs_stream import ElevenLabsStreamer
    
    streamer = ElevenLabsStreamer()
    async for chunk in streamer.stream_tts("Hello world!"):
        await play_audio(chunk)
"""

import asyncio
import os
import json
import base64
import logging
from typing import AsyncGenerator, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ElevenLabs configuration
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # "Adam" voice - fitting!
DEFAULT_MODEL_ID = "eleven_flash_v2_5"  # Lowest latency model

# WebSocket endpoint
WEBSOCKET_URL = "wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input"


@dataclass
class VoiceSettings:
    """ElevenLabs voice settings."""
    stability: float = 0.5
    similarity_boost: float = 0.8
    style: float = 0.0
    use_speaker_boost: bool = True


@dataclass  
class GenerationConfig:
    """ElevenLabs generation configuration."""
    # Chunk length schedule - controls buffering vs latency
    # Lower values = lower latency but potentially less smooth
    chunk_length_schedule: list = None
    
    def __post_init__(self):
        if self.chunk_length_schedule is None:
            # Default: start generating quickly, then buffer more
            self.chunk_length_schedule = [120, 160, 250, 290]


class ElevenLabsStreamer:
    """
    Real-time streaming TTS using ElevenLabs WebSocket API.
    
    Features:
    - Low-latency streaming with eleven_flash_v2_5 model
    - Configurable voice settings
    - Async generator for audio chunks
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: str = DEFAULT_VOICE_ID,
        model_id: str = DEFAULT_MODEL_ID,
        voice_settings: Optional[VoiceSettings] = None,
        generation_config: Optional[GenerationConfig] = None,
    ):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key required. Set ELEVENLABS_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.voice_id = voice_id
        self.model_id = model_id
        self.voice_settings = voice_settings or VoiceSettings()
        self.generation_config = generation_config or GenerationConfig()
        
        self._websocket = None
    
    @property
    def websocket_url(self) -> str:
        """Get WebSocket URL for current voice."""
        base_url = WEBSOCKET_URL.format(voice_id=self.voice_id)
        return f"{base_url}?model_id={self.model_id}"
    
    async def stream_tts(
        self,
        text: str,
        on_chunk: Optional[Callable[[bytes], None]] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS audio for given text.
        
        Args:
            text: Text to convert to speech
            on_chunk: Optional callback for each audio chunk
            
        Yields:
            Audio chunks as bytes (MP3 format)
        """
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package required. Install with: pip install websockets")
        
        logger.info(f"Starting TTS stream for: {text[:50]}...")
        
        try:
            async with websockets.connect(self.websocket_url) as ws:
                # Send initialization message
                init_message = {
                    "text": " ",  # Initial space to start
                    "voice_settings": {
                        "stability": self.voice_settings.stability,
                        "similarity_boost": self.voice_settings.similarity_boost,
                        "style": self.voice_settings.style,
                        "use_speaker_boost": self.voice_settings.use_speaker_boost,
                    },
                    "generation_config": {
                        "chunk_length_schedule": self.generation_config.chunk_length_schedule,
                    },
                    "xi_api_key": self.api_key,
                }
                await ws.send(json.dumps(init_message))
                
                # Send the actual text
                text_message = {"text": text}
                await ws.send(json.dumps(text_message))
                
                # Send end-of-stream signal
                end_message = {"text": ""}
                await ws.send(json.dumps(end_message))
                
                # Receive audio chunks
                total_chunks = 0
                total_bytes = 0
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        
                        if "audio" in data and data["audio"]:
                            # Decode base64 audio chunk
                            audio_chunk = base64.b64decode(data["audio"])
                            total_chunks += 1
                            total_bytes += len(audio_chunk)
                            
                            if on_chunk:
                                on_chunk(audio_chunk)
                            
                            yield audio_chunk
                        
                        if data.get("isFinal"):
                            logger.info(
                                f"TTS complete: {total_chunks} chunks, "
                                f"{total_bytes} bytes"
                            )
                            break
                        
                        if "error" in data:
                            logger.error(f"ElevenLabs error: {data['error']}")
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse message: {message[:100]}")
                        
        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
            raise
    
    async def stream_tts_to_bytes(self, text: str) -> bytes:
        """
        Stream TTS and return complete audio as bytes.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Complete audio as bytes (MP3 format)
        """
        audio_data = bytearray()
        
        async for chunk in self.stream_tts(text):
            audio_data.extend(chunk)
        
        return bytes(audio_data)
    
    async def stream_tts_to_file(self, text: str, output_path: str) -> str:
        """
        Stream TTS and save to file.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            
        Returns:
            Path to saved file
        """
        audio_data = await self.stream_tts_to_bytes(text)
        
        with open(output_path, "wb") as f:
            f.write(audio_data)
        
        logger.info(f"Saved {len(audio_data)} bytes to {output_path}")
        return output_path


class ElevenLabsStreamPlayer:
    """
    Convenience class to stream TTS directly to audio output.
    
    Combines ElevenLabsStreamer with K1Audio for seamless playback.
    """
    
    def __init__(
        self,
        streamer: Optional[ElevenLabsStreamer] = None,
        **streamer_kwargs
    ):
        self.streamer = streamer or ElevenLabsStreamer(**streamer_kwargs)
        self._audio_buffer = bytearray()
        self._playback_task: Optional[asyncio.Task] = None
    
    async def speak(
        self,
        text: str,
        audio_player: Optional[Callable[[bytes], asyncio.Future]] = None,
    ) -> None:
        """
        Speak text with streaming playback.
        
        Args:
            text: Text to speak
            audio_player: Async function to play audio chunks
        """
        if audio_player:
            # Stream directly to player
            async for chunk in self.streamer.stream_tts(text):
                await audio_player(chunk)
        else:
            # Buffer and play locally
            audio_data = await self.streamer.stream_tts_to_bytes(text)
            await self._play_local(audio_data)
    
    async def _play_local(self, audio_data: bytes) -> None:
        """Play audio locally using sounddevice/pydub."""
        try:
            # Try pydub for MP3 decoding
            from pydub import AudioSegment
            from pydub.playback import play
            import io
            
            audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            await asyncio.to_thread(play, audio)
            
        except ImportError:
            # Fallback: save to temp file and play with system player
            import tempfile
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            try:
                # Try different players
                for player in ["afplay", "mpv", "aplay", "paplay"]:
                    try:
                        await asyncio.to_thread(
                            subprocess.run,
                            [player, temp_path],
                            check=True,
                            capture_output=True
                        )
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            finally:
                import os
                os.unlink(temp_path)


async def stream_speak(
    text: str,
    voice_id: str = DEFAULT_VOICE_ID,
    api_key: Optional[str] = None,
) -> bytes:
    """
    Convenience function to stream TTS.
    
    Args:
        text: Text to speak
        voice_id: ElevenLabs voice ID
        api_key: API key (or use ELEVENLABS_API_KEY env var)
        
    Returns:
        Complete audio as bytes
    """
    streamer = ElevenLabsStreamer(
        api_key=api_key,
        voice_id=voice_id,
    )
    return await streamer.stream_tts_to_bytes(text)


async def main():
    """Test ElevenLabs streaming TTS."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ElevenLabs Streaming TTS")
    parser.add_argument("text", nargs="?", default="Hey there! I'm Adam, ready to play some sports!", 
                       help="Text to speak")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE_ID, help="Voice ID")
    parser.add_argument("--output", type=str, help="Save to file instead of playing")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_ID, help="Model ID")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    streamer = ElevenLabsStreamer(
        voice_id=args.voice,
        model_id=args.model,
    )
    
    if args.output:
        await streamer.stream_tts_to_file(args.text, args.output)
        print(f"Saved to {args.output}")
    else:
        player = ElevenLabsStreamPlayer(streamer=streamer)
        print(f"Speaking: {args.text}")
        await player.speak(args.text)
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
