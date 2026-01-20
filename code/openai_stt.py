#!/usr/bin/env python3
"""
OpenAI Realtime API - Speech-to-Text streaming.

Uses OpenAI's Realtime API for low-latency speech recognition.

Usage:
    from openai_stt import OpenAIRealtimeSTT
    
    stt = OpenAIRealtimeSTT()
    transcript = await stt.listen(duration=5.0)
    print(f"You said: {transcript}")
    
    # Or with streaming
    async for text in stt.stream_listen():
        print(f"Partial: {text}")
"""

import asyncio
import os
import json
import base64
import logging
from typing import AsyncGenerator, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# OpenAI Realtime API configuration
REALTIME_API_URL = "wss://api.openai.com/v1/realtime"
DEFAULT_MODEL = "gpt-4o-realtime-preview-2024-12-17"

# Audio configuration - must match OpenAI requirements
SAMPLE_RATE = 24000  # 24kHz
CHANNELS = 1  # Mono
SAMPLE_WIDTH = 2  # 16-bit PCM
CHUNK_MS = 40  # 40ms chunks


@dataclass
class RealtimeConfig:
    """OpenAI Realtime API configuration."""
    model: str = DEFAULT_MODEL
    modalities: list = None
    voice: str = "alloy"  # Not used for STT-only, but required
    input_audio_format: str = "pcm16"
    output_audio_format: str = "pcm16"
    turn_detection: dict = None
    
    def __post_init__(self):
        if self.modalities is None:
            self.modalities = ["text", "audio"]
        if self.turn_detection is None:
            # Server-side voice activity detection
            self.turn_detection = {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500,
            }


class OpenAIRealtimeSTT:
    """
    OpenAI Realtime API for speech-to-text.
    
    Features:
    - Low-latency streaming transcription
    - Voice activity detection (VAD)
    - Continuous listening mode
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[RealtimeConfig] = None,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.config = config or RealtimeConfig()
        self._websocket = None
        self._listening = False
        self._current_transcript = ""
    
    async def _connect(self):
        """Establish WebSocket connection."""
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package required. Install with: pip install websockets")
        
        url = f"{REALTIME_API_URL}?model={self.config.model}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        
        self._websocket = await websockets.connect(
            url,
            additional_headers=headers,
        )
        
        # Configure session
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": self.config.modalities,
                "voice": self.config.voice,
                "input_audio_format": self.config.input_audio_format,
                "output_audio_format": self.config.output_audio_format,
                "turn_detection": self.config.turn_detection,
            }
        }
        await self._websocket.send(json.dumps(session_config))
        
        # Wait for session confirmation
        response = await self._websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "error":
            raise Exception(f"Session error: {data.get('error', {}).get('message')}")
        
        logger.info("OpenAI Realtime session established")
    
    async def _disconnect(self):
        """Close WebSocket connection."""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
    
    async def send_audio(self, audio_data: bytes) -> None:
        """
        Send audio data to the API.
        
        Args:
            audio_data: Raw PCM audio (16-bit, 24kHz, mono)
        """
        if not self._websocket:
            await self._connect()
        
        # Encode audio as base64
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")
        
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }
        await self._websocket.send(json.dumps(message))
    
    async def commit_audio(self) -> None:
        """Signal end of audio input."""
        if self._websocket:
            message = {"type": "input_audio_buffer.commit"}
            await self._websocket.send(json.dumps(message))
    
    async def listen(
        self,
        audio_source: Optional[Callable[[], AsyncGenerator[bytes, None]]] = None,
        duration: float = 5.0,
        on_partial: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Listen for speech and return transcript.
        
        Args:
            audio_source: Async generator yielding audio chunks
            duration: Maximum listen duration (if no audio_source)
            on_partial: Callback for partial transcripts
            
        Returns:
            Final transcript
        """
        await self._connect()
        
        try:
            self._listening = True
            self._current_transcript = ""
            
            # Start audio input task
            if audio_source:
                audio_task = asyncio.create_task(
                    self._send_audio_stream(audio_source)
                )
            else:
                audio_task = asyncio.create_task(
                    self._capture_and_send_local(duration)
                )
            
            # Process responses
            transcript = await self._process_responses(
                timeout=duration + 5.0,
                on_partial=on_partial,
            )
            
            # Clean up
            audio_task.cancel()
            try:
                await audio_task
            except asyncio.CancelledError:
                pass
            
            return transcript
            
        finally:
            self._listening = False
            await self._disconnect()
    
    async def _send_audio_stream(
        self,
        audio_source: Callable[[], AsyncGenerator[bytes, None]]
    ) -> None:
        """Send audio from async generator."""
        async for chunk in audio_source():
            if not self._listening:
                break
            await self.send_audio(chunk)
        
        await self.commit_audio()
    
    async def _capture_and_send_local(self, duration: float) -> None:
        """Capture audio locally and send."""
        try:
            import sounddevice as sd
            import numpy as np
            
            chunk_frames = int(SAMPLE_RATE * CHUNK_MS / 1000)
            total_frames = int(SAMPLE_RATE * duration)
            frames_sent = 0
            
            def callback(indata, frames, time, status):
                nonlocal frames_sent
                if status:
                    logger.warning(f"Audio status: {status}")
                if self._listening and frames_sent < total_frames:
                    # Convert to 16-bit PCM
                    audio_int16 = (indata[:, 0] * 32768).astype(np.int16)
                    asyncio.create_task(self.send_audio(audio_int16.tobytes()))
                    frames_sent += frames
            
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=np.float32,
                blocksize=chunk_frames,
                callback=callback,
            ):
                await asyncio.sleep(duration)
            
            await self.commit_audio()
            
        except ImportError:
            logger.error("sounddevice not installed for local capture")
        except Exception as e:
            logger.error(f"Local capture error: {e}")
    
    async def _process_responses(
        self,
        timeout: float,
        on_partial: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Process WebSocket responses and extract transcript."""
        final_transcript = ""
        
        try:
            async with asyncio.timeout(timeout):
                while self._listening:
                    try:
                        message = await self._websocket.recv()
                        data = json.loads(message)
                        
                        event_type = data.get("type", "")
                        
                        # Handle different event types
                        if event_type == "conversation.item.input_audio_transcription.completed":
                            transcript = data.get("transcript", "")
                            if transcript:
                                final_transcript = transcript
                                logger.info(f"Transcript: {transcript}")
                        
                        elif event_type == "response.audio_transcript.delta":
                            delta = data.get("delta", "")
                            if delta and on_partial:
                                on_partial(delta)
                        
                        elif event_type == "response.audio_transcript.done":
                            transcript = data.get("transcript", "")
                            if transcript:
                                final_transcript = transcript
                        
                        elif event_type == "input_audio_buffer.speech_started":
                            logger.debug("Speech detected")
                        
                        elif event_type == "input_audio_buffer.speech_stopped":
                            logger.debug("Speech ended")
                            # Give a moment for transcription to complete
                            await asyncio.sleep(0.5)
                            if final_transcript:
                                break
                        
                        elif event_type == "error":
                            error = data.get("error", {})
                            logger.error(f"API error: {error.get('message')}")
                            break
                        
                    except asyncio.CancelledError:
                        break
                        
        except asyncio.TimeoutError:
            logger.debug("Listen timeout reached")
        
        return final_transcript
    
    async def stream_listen(
        self,
        audio_source: Optional[Callable[[], AsyncGenerator[bytes, None]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream transcripts as they're recognized.
        
        Args:
            audio_source: Async generator yielding audio chunks
            
        Yields:
            Partial and final transcripts
        """
        await self._connect()
        
        try:
            self._listening = True
            
            # Start audio capture
            if audio_source:
                audio_task = asyncio.create_task(
                    self._send_audio_stream(audio_source)
                )
            else:
                # Use local microphone
                audio_task = asyncio.create_task(
                    self._capture_local_continuous()
                )
            
            # Process and yield transcripts
            while self._listening:
                try:
                    message = await asyncio.wait_for(
                        self._websocket.recv(),
                        timeout=30.0
                    )
                    data = json.loads(message)
                    
                    event_type = data.get("type", "")
                    
                    if event_type == "conversation.item.input_audio_transcription.completed":
                        transcript = data.get("transcript", "")
                        if transcript:
                            yield transcript
                    
                    elif event_type == "response.audio_transcript.delta":
                        delta = data.get("delta", "")
                        if delta:
                            yield delta
                    
                    elif event_type == "error":
                        error = data.get("error", {})
                        logger.error(f"API error: {error.get('message')}")
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    logger.debug("Sending keepalive")
                    await self._websocket.ping()
                    
        finally:
            self._listening = False
            audio_task.cancel()
            try:
                await audio_task
            except asyncio.CancelledError:
                pass
            await self._disconnect()
    
    async def _capture_local_continuous(self) -> None:
        """Continuously capture and send local audio."""
        try:
            import sounddevice as sd
            import numpy as np
            
            chunk_frames = int(SAMPLE_RATE * CHUNK_MS / 1000)
            
            def callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio status: {status}")
                if self._listening:
                    audio_int16 = (indata[:, 0] * 32768).astype(np.int16)
                    asyncio.create_task(self.send_audio(audio_int16.tobytes()))
            
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=np.float32,
                blocksize=chunk_frames,
                callback=callback,
            ):
                while self._listening:
                    await asyncio.sleep(0.1)
                    
        except ImportError:
            logger.error("sounddevice not installed")
        except Exception as e:
            logger.error(f"Continuous capture error: {e}")
    
    def stop(self) -> None:
        """Stop listening."""
        self._listening = False


async def listen_once(
    duration: float = 5.0,
    api_key: Optional[str] = None,
) -> str:
    """
    Convenience function to listen for speech once.
    
    Args:
        duration: Maximum listen duration
        api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        
    Returns:
        Transcript
    """
    stt = OpenAIRealtimeSTT(api_key=api_key)
    return await stt.listen(duration=duration)


async def main():
    """Test OpenAI Realtime STT."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenAI Realtime Speech-to-Text")
    parser.add_argument("--duration", type=float, default=5.0, help="Listen duration in seconds")
    parser.add_argument("--continuous", action="store_true", help="Continuous listening mode")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    stt = OpenAIRealtimeSTT()
    
    if args.continuous:
        print("Listening continuously (Ctrl+C to stop)...")
        try:
            async for transcript in stt.stream_listen():
                print(f">>> {transcript}")
        except KeyboardInterrupt:
            print("\nStopped")
    else:
        print(f"Listening for {args.duration} seconds...")
        transcript = await stt.listen(duration=args.duration)
        print(f"\nYou said: {transcript}")


if __name__ == "__main__":
    asyncio.run(main())
