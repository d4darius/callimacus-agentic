import { useEffect, useRef } from "react";

interface AudioStreamerProps {
  isSessionActive: boolean;
}

function AudioStreamer({ isSessionActive }: AudioStreamerProps) {
  const socketRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  useEffect(() => {
    // If the session is turned OFF, aggressively shut down the PCM pipeline
    if (!isSessionActive) {
      if (processorRef.current) {
        processorRef.current.disconnect();
      }
      if (
        audioContextRef.current &&
        audioContextRef.current.state !== "closed"
      ) {
        audioContextRef.current.close();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
      return;
    }

    // If the session is turned ON, boot up the pipeline!
    let isMounted = true;

    const startStreaming = async () => {
      try {
        // 1. Open the WebSocket to FastAPI
        const ws = new WebSocket("ws://localhost:8000/api/ws/audio");
        socketRef.current = ws;

        ws.onopen = () => console.log("🎤 WebSocket Connected");
        ws.onclose = () => console.log("🎤 WebSocket Disconnected");

        // 2. Listen for text coming BACK from Python and broadcast it
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.text) {
            window.dispatchEvent(
              new CustomEvent("injectAudio", { detail: data.text }),
            );
          }
        };

        // 3. Request Microphone permissions
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        if (!isMounted) return;
        streamRef.current = stream;

        // 4. Create the Raw PCM Audio Context (with Safari Fallback)
        const AudioContextClass =
          window.AudioContext || (window as any).webkitAudioContext;
        const audioContext = new AudioContextClass({ sampleRate: 16000 });
        audioContextRef.current = audioContext;

        // 💡 THE FIX: Force the browser to wake up the audio context!
        if (audioContext.state === "suspended") {
          await audioContext.resume();
        }

        // 5. Connect the microphone to the script processor
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        processorRef.current = processor;

        processor.onaudioprocess = (e) => {
          if (ws.readyState === WebSocket.OPEN) {
            const float32Array = e.inputBuffer.getChannelData(0);
            const int16Array = new Int16Array(float32Array.length);
            for (let i = 0; i < float32Array.length; i++) {
              let s = Math.max(-1, Math.min(1, float32Array[i]));
              int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
            }
            ws.send(int16Array.buffer);
          }
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
      } catch (err) {
        console.error("Microphone access denied or WebSocket failed:", err);
      }
    };

    startStreaming();

    // Cleanup function when component unmounts or session toggles off
    return () => {
      isMounted = false;
      if (processorRef.current) processorRef.current.disconnect();
      if (
        audioContextRef.current &&
        audioContextRef.current.state !== "closed"
      ) {
        audioContextRef.current.close();
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      socketRef.current?.close();
    };
  }, [isSessionActive]);

  return null;
}

export default AudioStreamer;
