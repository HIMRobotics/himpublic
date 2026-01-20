#!/usr/bin/env python3
"""
Realtime Voice Conversation System for Adam.

Integrates:
- K1 Audio (speaker/microphone)
- OpenAI Realtime API (speech-to-text)
- Sports Responder (GPT-4 personality)
- ElevenLabs Streaming (text-to-speech)

Usage:
    python realtime_voice.py --talk        # Start conversation
    python realtime_voice.py --discover    # Discover audio interfaces
    python realtime_voice.py --test-tts    # Test TTS only
    python realtime_voice.py --test-stt    # Test STT only
"""

import asyncio
import os
import sys
import logging
import argparse
from typing import Optional
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from k1_audio import K1Audio, discover_audio_interfaces
from openai_stt import OpenAIRealtimeSTT
from elevenlabs_stream import ElevenLabsStreamer, ElevenLabsStreamPlayer
from sports_responder import SportsResponder

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_ROBOT_IP = "192.168.1.100"
LISTEN_DURATION = 10.0  # Max listen duration per turn
CONVERSATION_TIMEOUT = 300.0  # 5 minute conversation timeout


class RealtimeVoiceSystem:
    """
    Complete realtime voice conversation system.
    
    Connects STT -> LLM -> TTS for natural conversation flow.
    """
    
    def __init__(
        self,
        robot_ip: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.robot_ip = robot_ip or os.environ.get("K1_ROBOT_IP", DEFAULT_ROBOT_IP)
        
        # Initialize components (lazy)
        self._k1_audio: Optional[K1Audio] = None
        self._stt: Optional[OpenAIRealtimeSTT] = None
        self._tts: Optional[ElevenLabsStreamer] = None
        self._responder: Optional[SportsResponder] = None
        
        # Store API keys
        self._elevenlabs_key = elevenlabs_api_key
        self._openai_key = openai_api_key
        
        self._initialized = False
        self._running = False
    
    @property
    def k1_audio(self) -> K1Audio:
        """Get K1 audio interface."""
        if self._k1_audio is None:
            self._k1_audio = K1Audio(robot_ip=self.robot_ip)
        return self._k1_audio
    
    @property
    def stt(self) -> OpenAIRealtimeSTT:
        """Get STT instance."""
        if self._stt is None:
            self._stt = OpenAIRealtimeSTT(api_key=self._openai_key)
        return self._stt
    
    @property
    def tts(self) -> ElevenLabsStreamer:
        """Get TTS instance."""
        if self._tts is None:
            self._tts = ElevenLabsStreamer(api_key=self._elevenlabs_key)
        return self._tts
    
    @property
    def responder(self) -> SportsResponder:
        """Get responder instance."""
        if self._responder is None:
            self._responder = SportsResponder(api_key=self._openai_key)
        return self._responder
    
    async def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if initialization successful
        """
        logger.info("Initializing realtime voice system...")
        
        try:
            # Discover audio interface
            audio_method = await self.k1_audio.discover()
            logger.info(f"Audio interface: {audio_method}")
            
            # Verify API keys
            if not os.environ.get("OPENAI_API_KEY") and not self._openai_key:
                logger.error("OPENAI_API_KEY not set!")
                return False
            
            if not os.environ.get("ELEVENLABS_API_KEY") and not self._elevenlabs_key:
                logger.error("ELEVENLABS_API_KEY not set!")
                return False
            
            self._initialized = True
            logger.info("Initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def speak(self, text: str) -> bool:
        """
        Speak text through K1 speaker.
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        logger.info(f"Speaking: {text}")
        
        try:
            # Stream TTS to bytes
            audio_data = await self.tts.stream_tts_to_bytes(text)
            
            # Play through K1 (or fallback)
            # Note: ElevenLabs outputs MP3, K1Audio expects PCM
            # For now, use local playback which handles MP3
            player = ElevenLabsStreamPlayer(streamer=self.tts)
            await player._play_local(audio_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Speech failed: {e}")
            return False
    
    async def listen(self, duration: float = LISTEN_DURATION) -> str:
        """
        Listen for speech.
        
        Args:
            duration: Maximum listen duration
            
        Returns:
            Recognized text
        """
        logger.info(f"Listening for {duration} seconds...")
        
        try:
            transcript = await self.stt.listen(duration=duration)
            logger.info(f"Heard: {transcript}")
            return transcript
            
        except Exception as e:
            logger.error(f"Listen failed: {e}")
            return ""
    
    async def conversation_turn(self) -> tuple[str, str]:
        """
        Execute one conversation turn.
        
        Returns:
            Tuple of (user_text, adam_response)
        """
        # Listen for user
        user_text = await self.listen()
        
        if not user_text:
            return "", ""
        
        # Generate response
        adam_response = await self.responder.respond(user_text)
        
        # Speak response
        await self.speak(adam_response)
        
        return user_text, adam_response
    
    async def run_conversation(
        self,
        greeting: bool = True,
        timeout: float = CONVERSATION_TIMEOUT,
    ) -> None:
        """
        Run interactive conversation loop.
        
        Args:
            greeting: Whether to greet at start
            timeout: Total conversation timeout
        """
        if not self._initialized:
            if not await self.initialize():
                logger.error("Failed to initialize, cannot start conversation")
                return
        
        self._running = True
        
        print("\n" + "=" * 50)
        print("ADAM VOICE CONVERSATION")
        print("=" * 50)
        print(f"Audio: {self.k1_audio.audio_method}")
        print("Press Ctrl+C to stop")
        print("=" * 50 + "\n")
        
        try:
            # Initial greeting
            if greeting:
                await self.speak("Hey! Great to see you! Ready to chat?")
            
            start_time = asyncio.get_event_loop().time()
            
            while self._running:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    logger.info("Conversation timeout reached")
                    await self.speak("Great talking with you! Catch you later!")
                    break
                
                # Do one conversation turn
                user_text, adam_response = await self.conversation_turn()
                
                if user_text:
                    print(f"You: {user_text}")
                    print(f"Adam: {adam_response}\n")
                
                # Check for exit commands
                if user_text.lower() in ["bye", "goodbye", "quit", "exit", "stop"]:
                    await self.speak("See you next time, champ!")
                    break
                
                # Small pause between turns
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\nConversation ended by user")
            await self.speak("Catch you later!")
        except Exception as e:
            logger.error(f"Conversation error: {e}")
        finally:
            self._running = False
    
    def stop(self) -> None:
        """Stop the conversation."""
        self._running = False
        if self._stt:
            self._stt.stop()


async def test_tts(text: str = "Hey there! I'm Adam, and I'm ready to play some sports!"):
    """Test TTS functionality."""
    print(f"Testing TTS: {text}")
    
    streamer = ElevenLabsStreamer()
    player = ElevenLabsStreamPlayer(streamer=streamer)
    
    await player.speak(text)
    print("TTS test complete!")


async def test_stt(duration: float = 5.0):
    """Test STT functionality."""
    print(f"Testing STT for {duration} seconds...")
    print("Speak now!")
    
    stt = OpenAIRealtimeSTT()
    transcript = await stt.listen(duration=duration)
    
    print(f"\nYou said: {transcript}")
    print("STT test complete!")


async def test_responder():
    """Test responder functionality."""
    print("Testing Sports Responder...")
    
    responder = SportsResponder()
    
    test_inputs = [
        "Hey Adam!",
        "I just won the game!",
        "We lost today...",
    ]
    
    for user_input in test_inputs:
        response = await responder.respond(user_input)
        print(f"User: {user_input}")
        print(f"Adam: {response}\n")
    
    print("Responder test complete!")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Adam Realtime Voice Conversation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python realtime_voice.py --talk           Start conversation with Adam
  python realtime_voice.py --discover       Discover audio interfaces
  python realtime_voice.py --test-tts       Test text-to-speech
  python realtime_voice.py --test-stt       Test speech-to-text
  python realtime_voice.py --test-responder Test GPT-4 responder

Environment Variables:
  OPENAI_API_KEY       OpenAI API key (required)
  ELEVENLABS_API_KEY   ElevenLabs API key (required)
  K1_ROBOT_IP          Robot IP address (default: 192.168.1.100)
        """
    )
    
    parser.add_argument("--talk", "-t", action="store_true",
                       help="Start conversation")
    parser.add_argument("--discover", "-d", action="store_true",
                       help="Discover audio interfaces")
    parser.add_argument("--test-tts", action="store_true",
                       help="Test text-to-speech")
    parser.add_argument("--test-stt", action="store_true",
                       help="Test speech-to-text")
    parser.add_argument("--test-responder", action="store_true",
                       help="Test GPT-4 responder")
    parser.add_argument("--robot-ip", type=str,
                       help="Robot IP address")
    parser.add_argument("--no-greeting", action="store_true",
                       help="Skip initial greeting")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Reduce noise from other loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    try:
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
        
        elif args.test_tts:
            await test_tts()
        
        elif args.test_stt:
            await test_stt()
        
        elif args.test_responder:
            await test_responder()
        
        elif args.talk:
            system = RealtimeVoiceSystem(robot_ip=args.robot_ip)
            await system.run_conversation(greeting=not args.no_greeting)
        
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
