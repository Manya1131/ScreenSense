"""
audio_utils.py
--------------
Asynchronous Text-to-Speech utility to provide audio cues without blocking the main thread.
Uses native Windows SAPI to avoid pyttsx3 thread-hanging bugs.
"""

import threading
import queue

class Speaker:
    def __init__(self):
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        # We use native Windows SAPI directly because pyttsx3 has a known bug 
        # where it hangs on the second utterance when used in a background thread.
        try:
            import pythoncom
            import win32com.client
            
            # COM must be initialized for this background thread
            pythoncom.CoInitialize()
            engine = win32com.client.Dispatch("SAPI.SpVoice")
            
            while True:
                text = self.q.get()
                if text is None:
                    break
                try:
                    # Speak synchronously within this background thread
                    engine.Speak(text)
                except Exception as e:
                    print(f"Speech error: {e}")
                self.q.task_done()
        except Exception as e:
            print(f"Failed to initialize SAPI: {e}")

    def speak(self, text: str):
        # Only queue the message if the queue is empty or short, to avoid speech backlog
        if self.q.qsize() < 2:
            self.q.put(text)

# Global singleton
_speaker = Speaker()

def speak_text(text: str):
    """Adds text to the speech queue to be spoken asynchronously."""
    _speaker.speak(text)
