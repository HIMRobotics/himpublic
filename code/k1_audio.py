#!/usr/bin/env python3
"""
K1 Audio Interface - Speaker and Microphone access for Booster K1 robot.

Provides a unified interface with automatic discovery of available audio methods:
1. ROS2 topics (preferred)
2. SSH + ALSA (fallback)
3. Local audio (development fallback)

Usage:
    from k1_audio import K1Audio
    
    audio = K1Audio(robot_ip="192.168.1.100")
    await audio.discover()
    await audio.play_audio(audio_data)
    audio_data = await audio.capture_audio(duration=5.0)
"""

import asyncio
import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Literal, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Audio configuration
SAMPLE_RATE = 24000  # 24kHz for OpenAI Realtime API compatibility
CHANNELS = 1  # Mono
SAMPLE_WIDTH = 2  # 16-bit PCM
CHUNK_DURATION_MS = 40  # 40ms chunks for streaming


@dataclass
class AudioConfig:
    """Audio configuration settings."""
    sample_rate: int = SAMPLE_RATE
    channels: int = CHANNELS
    sample_width: int = SAMPLE_WIDTH
    chunk_size: int = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)


class K1Audio:
    """
    K1 Audio Interface with auto-discovery of available methods.
    
    Tries methods in order:
    1. ROS2 topics (if available)
    2. SSH + ALSA (if robot is accessible)
    3. Local audio (fallback for development)
    """
    
    def __init__(
        self,
        robot_ip: Optional[str] = None,
        ssh_user: str = "booster",
        ssh_password: Optional[str] = None,
    ):
        self.robot_ip = robot_ip or os.environ.get("K1_ROBOT_IP", "192.168.1.100")
        self.ssh_user = ssh_user or os.environ.get("K1_SSH_USER", "booster")
        self.ssh_password = ssh_password or os.environ.get("K1_SSH_PASSWORD")
        
        self.audio_method: Optional[Literal["ros2", "ssh_alsa", "local"]] = None
        self.config = AudioConfig()
        
        # ROS2 topic names (to be discovered)
        self.ros2_audio_out_topic: Optional[str] = None
        self.ros2_audio_in_topic: Optional[str] = None
        self.ros2_tts_service: Optional[str] = None
        
        # SSH connection (lazy init)
        self._ssh_client = None
        
        # Local audio stream
        self._local_stream = None
        
        self._discovered = False
    
    async def discover(self) -> str:
        """
        Discover available audio interface method.
        
        Returns:
            The discovered method: 'ros2', 'ssh_alsa', or 'local'
        """
        logger.info("Discovering K1 audio interface...")
        
        # Try ROS2 first
        if await self._discover_ros2():
            self.audio_method = "ros2"
            logger.info(f"Using ROS2 audio interface")
            self._discovered = True
            return self.audio_method
        
        # Try SSH + ALSA
        if await self._discover_ssh_alsa():
            self.audio_method = "ssh_alsa"
            logger.info(f"Using SSH + ALSA audio interface")
            self._discovered = True
            return self.audio_method
        
        # Fallback to local
        self.audio_method = "local"
        logger.info("Using local audio interface (fallback)")
        self._discovered = True
        return self.audio_method
    
    async def _discover_ros2(self) -> bool:
        """Check for ROS2 audio topics."""
        try:
            # Check if ROS2 is available
            result = await asyncio.to_thread(
                subprocess.run,
                ["ros2", "topic", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.debug("ROS2 not available or not configured")
                return False
            
            topics = result.stdout.strip().split("\n")
            
            # Look for audio-related topics
            audio_topics = [t for t in topics if "audio" in t.lower()]
            tts_topics = [t for t in topics if "tts" in t.lower() or "speech" in t.lower()]
            
            # Check for output topics
            for pattern in ["/audio_out", "/audio/play", "/speaker"]:
                matches = [t for t in audio_topics if pattern in t]
                if matches:
                    self.ros2_audio_out_topic = matches[0]
                    break
            
            # Check for input topics
            for pattern in ["/audio_in", "/mic", "/microphone"]:
                matches = [t for t in audio_topics if pattern in t]
                if matches:
                    self.ros2_audio_in_topic = matches[0]
                    break
            
            # Check for TTS service
            result = await asyncio.to_thread(
                subprocess.run,
                ["ros2", "service", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                services = result.stdout.strip().split("\n")
                for pattern in ["/tts", "/say", "/speak"]:
                    matches = [s for s in services if pattern in s.lower()]
                    if matches:
                        self.ros2_tts_service = matches[0]
                        break
            
            # We need at least audio output to use ROS2
            return self.ros2_audio_out_topic is not None or self.ros2_tts_service is not None
            
        except FileNotFoundError:
            logger.debug("ROS2 CLI not found")
            return False
        except subprocess.TimeoutExpired:
            logger.debug("ROS2 command timed out")
            return False
        except Exception as e:
            logger.debug(f"ROS2 discovery error: {e}")
            return False
    
    async def _discover_ssh_alsa(self) -> bool:
        """Check if we can access robot via SSH + ALSA."""
        try:
            # Try to connect and check for ALSA
            import paramiko
            
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": self.robot_ip,
                "username": self.ssh_user,
                "timeout": 5,
            }
            
            if self.ssh_password:
                connect_kwargs["password"] = self.ssh_password
            else:
                # Try key-based auth
                connect_kwargs["look_for_keys"] = True
            
            await asyncio.to_thread(client.connect, **connect_kwargs)
            
            # Check for ALSA devices
            stdin, stdout, stderr = await asyncio.to_thread(
                client.exec_command,
                "aplay -l 2>/dev/null | head -5"
            )
            output = await asyncio.to_thread(stdout.read)
            
            self._ssh_client = client
            
            if b"card" in output.lower():
                logger.debug(f"Found ALSA devices on robot: {output.decode()[:100]}")
                return True
            
            logger.debug("No ALSA devices found on robot")
            return False
            
        except ImportError:
            logger.debug("paramiko not installed, SSH not available")
            return False
        except Exception as e:
            logger.debug(f"SSH connection failed: {e}")
            return False
    
    async def play_audio(
        self,
        audio_data: bytes,
        sample_rate: Optional[int] = None,
        blocking: bool = True
    ) -> bool:
        """
        Play audio through K1 speaker.
        
        Args:
            audio_data: Raw PCM audio data (16-bit signed, little-endian)
            sample_rate: Sample rate (default: 24000)
            blocking: Wait for playback to complete
            
        Returns:
            True if playback started successfully
        """
        if not self._discovered:
            await self.discover()
        
        sample_rate = sample_rate or self.config.sample_rate
        
        try:
            if self.audio_method == "ros2":
                return await self._play_ros2(audio_data, sample_rate)
            elif self.audio_method == "ssh_alsa":
                return await self._play_ssh_alsa(audio_data, sample_rate, blocking)
            else:
                return await self._play_local(audio_data, sample_rate, blocking)
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
            return False
    
    async def _play_ros2(self, audio_data: bytes, sample_rate: int) -> bool:
        """Play audio via ROS2 topic."""
        try:
            # Use TTS service if available
            if self.ros2_tts_service:
                logger.warning("ROS2 TTS service found but not implemented yet")
                return False
            
            # Publish to audio topic
            if self.ros2_audio_out_topic:
                # Would need rclpy here - placeholder
                logger.warning("ROS2 audio topic publishing not implemented yet")
                return False
            
            return False
        except Exception as e:
            logger.error(f"ROS2 playback error: {e}")
            return False
    
    async def _play_ssh_alsa(
        self,
        audio_data: bytes,
        sample_rate: int,
        blocking: bool
    ) -> bool:
        """Play audio via SSH + ALSA."""
        try:
            if not self._ssh_client:
                logger.error("SSH client not connected")
                return False
            
            # Create aplay command
            # Format: signed 16-bit little-endian, mono
            cmd = f"aplay -f S16_LE -r {sample_rate} -c 1 -q -"
            
            stdin, stdout, stderr = await asyncio.to_thread(
                self._ssh_client.exec_command,
                cmd
            )
            
            # Write audio data to stdin
            await asyncio.to_thread(stdin.write, audio_data)
            await asyncio.to_thread(stdin.channel.shutdown_write)
            
            if blocking:
                # Wait for completion
                await asyncio.to_thread(stdout.read)
            
            return True
            
        except Exception as e:
            logger.error(f"SSH ALSA playback error: {e}")
            return False
    
    async def _play_local(
        self,
        audio_data: bytes,
        sample_rate: int,
        blocking: bool
    ) -> bool:
        """Play audio locally (fallback for development)."""
        try:
            import sounddevice as sd
            import numpy as np
            
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            if blocking:
                await asyncio.to_thread(
                    sd.play,
                    audio_float,
                    sample_rate
                )
                await asyncio.to_thread(sd.wait)
            else:
                await asyncio.to_thread(
                    sd.play,
                    audio_float,
                    sample_rate
                )
            
            return True
            
        except ImportError:
            logger.error("sounddevice not installed for local playback")
            return False
        except Exception as e:
            logger.error(f"Local playback error: {e}")
            return False
    
    async def capture_audio(
        self,
        duration: float = 5.0,
        callback: Optional[Callable[[bytes], None]] = None
    ) -> bytes:
        """
        Capture audio from K1 microphone.
        
        Args:
            duration: Recording duration in seconds
            callback: Optional callback for streaming chunks
            
        Returns:
            Raw PCM audio data
        """
        if not self._discovered:
            await self.discover()
        
        try:
            if self.audio_method == "ros2":
                return await self._capture_ros2(duration, callback)
            elif self.audio_method == "ssh_alsa":
                return await self._capture_ssh_alsa(duration, callback)
            else:
                return await self._capture_local(duration, callback)
        except Exception as e:
            logger.error(f"Audio capture failed: {e}")
            return b""
    
    async def _capture_ros2(
        self,
        duration: float,
        callback: Optional[Callable[[bytes], None]]
    ) -> bytes:
        """Capture audio via ROS2 topic."""
        logger.warning("ROS2 audio capture not implemented yet")
        return b""
    
    async def _capture_ssh_alsa(
        self,
        duration: float,
        callback: Optional[Callable[[bytes], None]]
    ) -> bytes:
        """Capture audio via SSH + ALSA."""
        try:
            if not self._ssh_client:
                logger.error("SSH client not connected")
                return b""
            
            # Create arecord command
            cmd = f"arecord -f S16_LE -r {self.config.sample_rate} -c 1 -d {int(duration)} -q -"
            
            stdin, stdout, stderr = await asyncio.to_thread(
                self._ssh_client.exec_command,
                cmd
            )
            
            if callback:
                # Stream chunks
                audio_data = bytearray()
                chunk_size = self.config.chunk_size * self.config.sample_width
                
                while True:
                    chunk = await asyncio.to_thread(stdout.read, chunk_size)
                    if not chunk:
                        break
                    audio_data.extend(chunk)
                    callback(bytes(chunk))
                
                return bytes(audio_data)
            else:
                # Read all at once
                return await asyncio.to_thread(stdout.read)
            
        except Exception as e:
            logger.error(f"SSH ALSA capture error: {e}")
            return b""
    
    async def _capture_local(
        self,
        duration: float,
        callback: Optional[Callable[[bytes], None]]
    ) -> bytes:
        """Capture audio locally (fallback for development)."""
        try:
            import sounddevice as sd
            import numpy as np
            
            frames = int(duration * self.config.sample_rate)
            
            if callback:
                # Stream with callback
                audio_data = bytearray()
                chunk_frames = self.config.chunk_size
                
                def audio_callback(indata, frames, time, status):
                    if status:
                        logger.warning(f"Audio status: {status}")
                    chunk = (indata[:, 0] * 32768).astype(np.int16).tobytes()
                    audio_data.extend(chunk)
                    callback(chunk)
                
                with sd.InputStream(
                    samplerate=self.config.sample_rate,
                    channels=1,
                    dtype=np.float32,
                    blocksize=chunk_frames,
                    callback=audio_callback
                ):
                    await asyncio.sleep(duration)
                
                return bytes(audio_data)
            else:
                # Record all at once
                recording = await asyncio.to_thread(
                    sd.rec,
                    frames,
                    samplerate=self.config.sample_rate,
                    channels=1,
                    dtype=np.float32
                )
                await asyncio.to_thread(sd.wait)
                
                # Convert to 16-bit PCM
                audio_int16 = (recording[:, 0] * 32768).astype(np.int16)
                return audio_int16.tobytes()
            
        except ImportError:
            logger.error("sounddevice not installed for local capture")
            return b""
        except Exception as e:
            logger.error(f"Local capture error: {e}")
            return b""
    
    async def start_streaming_capture(
        self,
        callback: Callable[[bytes], None]
    ) -> "AudioStreamHandle":
        """
        Start continuous audio capture with streaming callback.
        
        Args:
            callback: Called with each audio chunk
            
        Returns:
            Handle to stop streaming
        """
        if not self._discovered:
            await self.discover()
        
        return await AudioStreamHandle.start(self, callback)
    
    def close(self):
        """Clean up resources."""
        if self._ssh_client:
            try:
                self._ssh_client.close()
            except Exception:
                pass
            self._ssh_client = None
        
        if self._local_stream:
            try:
                self._local_stream.stop()
                self._local_stream.close()
            except Exception:
                pass
            self._local_stream = None


class AudioStreamHandle:
    """Handle for continuous audio streaming."""
    
    def __init__(self, audio: K1Audio, callback: Callable[[bytes], None]):
        self.audio = audio
        self.callback = callback
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stream = None
    
    @classmethod
    async def start(
        cls,
        audio: K1Audio,
        callback: Callable[[bytes], None]
    ) -> "AudioStreamHandle":
        """Start streaming capture."""
        handle = cls(audio, callback)
        await handle._start()
        return handle
    
    async def _start(self):
        """Internal start method."""
        self._running = True
        
        if self.audio.audio_method == "local":
            await self._start_local_stream()
        else:
            # For SSH/ROS2, use polling loop
            self._task = asyncio.create_task(self._stream_loop())
    
    async def _start_local_stream(self):
        """Start local audio stream."""
        try:
            import sounddevice as sd
            import numpy as np
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio status: {status}")
                if self._running:
                    chunk = (indata[:, 0] * 32768).astype(np.int16).tobytes()
                    self.callback(chunk)
            
            self._stream = sd.InputStream(
                samplerate=self.audio.config.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=self.audio.config.chunk_size,
                callback=audio_callback
            )
            self._stream.start()
            
        except Exception as e:
            logger.error(f"Failed to start local stream: {e}")
            self._running = False
    
    async def _stream_loop(self):
        """Streaming loop for SSH/ROS2."""
        chunk_duration = self.audio.config.chunk_size / self.audio.config.sample_rate
        
        while self._running:
            try:
                chunk = await self.audio.capture_audio(
                    duration=chunk_duration,
                    callback=None
                )
                if chunk:
                    self.callback(chunk)
            except Exception as e:
                logger.error(f"Stream loop error: {e}")
                await asyncio.sleep(0.1)
    
    async def stop(self):
        """Stop streaming capture."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None


async def discover_audio_interfaces(robot_ip: Optional[str] = None) -> dict:
    """
    Discover all available audio interfaces on the K1.
    
    Returns:
        Dictionary with discovery results
    """
    audio = K1Audio(robot_ip=robot_ip)
    method = await audio.discover()
    
    return {
        "method": method,
        "robot_ip": audio.robot_ip,
        "ros2_audio_out": audio.ros2_audio_out_topic,
        "ros2_audio_in": audio.ros2_audio_in_topic,
        "ros2_tts_service": audio.ros2_tts_service,
    }


async def main():
    """Test audio discovery and playback."""
    import argparse
    
    parser = argparse.ArgumentParser(description="K1 Audio Interface")
    parser.add_argument("--discover", action="store_true", help="Discover audio interfaces")
    parser.add_argument("--play", type=str, help="Play audio file")
    parser.add_argument("--record", type=float, help="Record audio for N seconds")
    parser.add_argument("--robot-ip", type=str, help="Robot IP address")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    if args.discover:
        print("Discovering audio interfaces...")
        result = await discover_audio_interfaces(args.robot_ip)
        print(f"\nDiscovery Results:")
        print(f"  Method: {result['method']}")
        print(f"  Robot IP: {result['robot_ip']}")
        if result['ros2_audio_out']:
            print(f"  ROS2 Audio Out: {result['ros2_audio_out']}")
        if result['ros2_audio_in']:
            print(f"  ROS2 Audio In: {result['ros2_audio_in']}")
        if result['ros2_tts_service']:
            print(f"  ROS2 TTS Service: {result['ros2_tts_service']}")
    
    elif args.play:
        audio = K1Audio(robot_ip=args.robot_ip)
        await audio.discover()
        
        print(f"Playing {args.play} via {audio.audio_method}...")
        with open(args.play, "rb") as f:
            audio_data = f.read()
        
        success = await audio.play_audio(audio_data)
        print(f"Playback {'succeeded' if success else 'failed'}")
    
    elif args.record:
        audio = K1Audio(robot_ip=args.robot_ip)
        await audio.discover()
        
        print(f"Recording {args.record}s via {audio.audio_method}...")
        data = await audio.capture_audio(duration=args.record)
        
        output_file = "recorded_audio.raw"
        with open(output_file, "wb") as f:
            f.write(data)
        print(f"Saved {len(data)} bytes to {output_file}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
