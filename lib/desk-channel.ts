// Lets the lesson window tell the study desk window which topic is open.
// Same-origin only: BroadcastChannel plus localStorage for a desk opened later.
const CHANNEL = "corelab-desk";
const KEY = "corelab:desk-topic";

export function announceTopic(topic: string) {
  try {
    localStorage.setItem(KEY, topic);
    const channel = new BroadcastChannel(CHANNEL);
    channel.postMessage({ topic });
    channel.close();
  } catch {
    // Private mode or an old browser: the desk falls back to its own picker.
  }
}

export function lastTopic() {
  try {
    return localStorage.getItem(KEY) ?? "";
  } catch {
    return "";
  }
}

export function onTopic(listener: (topic: string) => void) {
  let channel: BroadcastChannel | null = null;
  try {
    channel = new BroadcastChannel(CHANNEL);
    channel.onmessage = (e) => {
      if (typeof e.data?.topic === "string") listener(e.data.topic);
    };
  } catch {
    channel = null;
  }
  return () => channel?.close();
}
