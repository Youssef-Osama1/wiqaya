import { useCallback, useEffect, useState } from "react";

function getSynth() {
  if (typeof window === "undefined") return undefined;
  return window.speechSynthesis ?? undefined;
}

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);

  const isSupported = getSynth() !== undefined;

  const cancel = useCallback(() => {
    getSynth()?.cancel();
    setIsSpeaking(false);
  }, []);

  const speak = useCallback((text: string) => {
    const synth = getSynth();
    if (!synth || !text) return;

    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    synth.speak(utterance);
  }, []);

  // speechSynthesis is a browser-level singleton that outlives this component: without an
  // explicit cancel on unmount, audio keeps playing after the user switches tab or navigates.
  useEffect(() => () => getSynth()?.cancel(), []);

  return { isSupported, isSpeaking, speak, cancel };
}
