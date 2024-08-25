import { useState, useCallback } from 'preact/hooks';

interface GreetingProps {
  messages: string[];
}

export function Greeting({ messages }: GreetingProps) {
  const [greeting, setGreeting] = useState(messages[0]);

  const randomMessage = useCallback(
    () => messages[Math.floor(Math.random() * messages.length)],
    [messages],
  );

  return (
    <div>
      <h3>{greeting}! Thank you for visiting!</h3>
      <button onClick={() => setGreeting(randomMessage())}>New Greeting</button>
    </div>
  );
}
