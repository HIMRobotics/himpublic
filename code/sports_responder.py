#!/usr/bin/env python3
"""
Sports Responder - GPT-4 powered sports personality for Adam.

Generates dynamic, sports-themed responses with Adam's character.

Usage:
    from sports_responder import SportsResponder
    
    responder = SportsResponder()
    response = await responder.respond("I just scored a goal!")
    print(response)  # "GOOOAL! That's what I'm talking about! High five!"
"""

import asyncio
import os
import logging
from typing import Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Adam's character system prompt
ADAM_SYSTEM_PROMPT = """You are Adam, a friendly and athletic humanoid robot made by HIM Robotics. 

Your personality:
- Fun, approachable, and enthusiastic about sports
- You love football, basketball, soccer, tennis, and all athletics
- You're a hype man - you celebrate wins and encourage after losses
- You speak in short, energetic phrases (1-2 sentences max)
- You use sports metaphors and terminology naturally
- You're supportive and positive, like a great teammate
- You have a playful, competitive spirit

Keep responses SHORT (under 20 words) for natural conversation flow.
Never mention being an AI or language model - you're Adam the robot!

Examples of your style:
- "Hey! Great to see you! Ready to get pumped up?"
- "TOUCHDOWN! That's what I'm talking about!"
- "Aww tough break, but we'll get 'em next time!"
- "You crushed it out there! High five!"
- "Game on! Let's do this!"
- "Nice hustle! That's championship effort right there!"
- "MVP material, no doubt about it!"
- "Shake it off, champ. Every pro has bad days!"

When someone mentions a sport, get excited about it specifically.
When they mention winning/scoring, celebrate BIG.
When they mention losing/missing, be encouraging and supportive.
For general chat, be friendly and bring sports energy."""


@dataclass
class ConversationMessage:
    """A message in the conversation history."""
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ResponderConfig:
    """Configuration for the sports responder."""
    model: str = "gpt-4o"
    max_tokens: int = 50  # Keep responses short
    temperature: float = 0.9  # More personality variation
    max_history: int = 10  # Keep last N messages for context


class SportsResponder:
    """
    GPT-4 powered sports personality responder.
    
    Features:
    - Adam's character personality
    - Conversation memory
    - Context-aware responses
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[ResponderConfig] = None,
        system_prompt: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.config = config or ResponderConfig()
        self.system_prompt = system_prompt or ADAM_SYSTEM_PROMPT
        
        # Conversation history
        self.history: List[ConversationMessage] = []
        
        # OpenAI client (lazy init)
        self._client = None
    
    @property
    def client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")
        return self._client
    
    async def respond(
        self,
        user_input: str,
        context: Optional[str] = None,
    ) -> str:
        """
        Generate a response to user input.
        
        Args:
            user_input: What the user said
            context: Optional additional context
            
        Returns:
            Adam's response
        """
        # Build messages
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add context if provided
        if context:
            messages.append({
                "role": "system",
                "content": f"Context: {context}"
            })
        
        # Add conversation history
        for msg in self.history[-self.config.max_history:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            
            assistant_response = response.choices[0].message.content.strip()
            
            # Update history
            self.history.append(ConversationMessage(role="user", content=user_input))
            self.history.append(ConversationMessage(role="assistant", content=assistant_response))
            
            # Trim history if too long
            if len(self.history) > self.config.max_history * 2:
                self.history = self.history[-self.config.max_history * 2:]
            
            logger.info(f"Response: {assistant_response}")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback responses
            return self._fallback_response(user_input)
    
    def _fallback_response(self, user_input: str) -> str:
        """Generate fallback response if API fails."""
        user_lower = user_input.lower()
        
        # Check for common patterns
        if any(word in user_lower for word in ["score", "goal", "touchdown", "win", "won"]):
            return "YEAH! That's what I'm talking about!"
        elif any(word in user_lower for word in ["miss", "lose", "lost", "bad"]):
            return "Shake it off! We'll get 'em next time!"
        elif any(word in user_lower for word in ["hi", "hello", "hey"]):
            return "Hey there! Ready to have some fun?"
        elif any(word in user_lower for word in ["bye", "later", "goodbye"]):
            return "See you next time, champ!"
        else:
            return "Let's go! Game on!"
    
    async def respond_with_emotion(
        self,
        user_input: str,
    ) -> tuple[str, str]:
        """
        Generate response with detected emotion.
        
        Returns:
            Tuple of (response, emotion)
            Emotion is one of: "excited", "encouraging", "friendly", "celebratory"
        """
        response = await self.respond(user_input)
        
        # Simple emotion detection based on response
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["yeah", "goal", "touchdown", "awesome", "!"]):
            emotion = "celebratory"
        elif any(word in response_lower for word in ["next time", "shake", "got this"]):
            emotion = "encouraging"
        elif any(word in response_lower for word in ["let's go", "game on", "ready"]):
            emotion = "excited"
        else:
            emotion = "friendly"
        
        return response, emotion
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history.clear()
    
    def add_context(self, context: str) -> None:
        """Add context to conversation history."""
        self.history.append(ConversationMessage(
            role="system",
            content=f"Context: {context}"
        ))


# Pre-defined response categories for quick responses without API
QUICK_RESPONSES = {
    "greeting": [
        "Hey there! Ready to get pumped up?",
        "What's up! Let's have some fun!",
        "Hey! Good to see you!",
    ],
    "celebrate": [
        "GOOOAL! That's what I'm talking about!",
        "YES! Absolutely crushed it!",
        "TOUCHDOWN! MVP right there!",
        "Incredible! High five!",
    ],
    "encourage": [
        "Shake it off! We'll get 'em next time!",
        "Hey, every champion has tough moments!",
        "Stay strong! You've got this!",
        "Just a warmup! The real game starts now!",
    ],
    "farewell": [
        "See you next time, champ!",
        "Later! Keep crushing it!",
        "Catch you on the flip side!",
    ],
}


def get_quick_response(category: str) -> str:
    """Get a random quick response from category."""
    import random
    responses = QUICK_RESPONSES.get(category, QUICK_RESPONSES["greeting"])
    return random.choice(responses)


async def respond_quick(user_input: str, api_key: Optional[str] = None) -> str:
    """
    Quick convenience function for single response.
    
    Args:
        user_input: What the user said
        api_key: OpenAI API key
        
    Returns:
        Adam's response
    """
    responder = SportsResponder(api_key=api_key)
    return await responder.respond(user_input)


async def main():
    """Test sports responder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Adam Sports Responder")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Interactive conversation mode")
    parser.add_argument("text", nargs="?", help="Text to respond to")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    responder = SportsResponder()
    
    if args.interactive:
        print("=" * 50)
        print("ADAM SPORTS RESPONDER")
        print("=" * 50)
        print("Chat with Adam! Type 'quit' to exit.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\nAdam: See you next time, champ!")
                    break
                
                if not user_input:
                    continue
                
                response = await responder.respond(user_input)
                print(f"Adam: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nAdam: Catch you later!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    elif args.text:
        response = await responder.respond(args.text)
        print(f"Adam: {response}")
    
    else:
        # Demo responses
        print("Demo responses:\n")
        
        test_inputs = [
            "Hey Adam!",
            "I just scored a goal!",
            "We lost the game today...",
            "Want to play some basketball?",
            "I'm training for a marathon",
        ]
        
        for user_input in test_inputs:
            response = await responder.respond(user_input)
            print(f"User: {user_input}")
            print(f"Adam: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
