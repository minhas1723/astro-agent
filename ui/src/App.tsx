import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import { Chat } from "@/components/chat";

import { ChatProvider } from "@/contexts/ChatContext";
import { UserProvider, useUser } from "@/contexts/UserContext";
import { OnboardingWizard } from "@/components/OnboardingWizard";

function Home() {
  const { isOnboarded } = useUser();

  if (!isOnboarded) {
    return <OnboardingWizard />;
  }

  return (
    <ChatProvider>
      <Chat />
    </ChatProvider>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <UserProvider>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </UserProvider>
    </BrowserRouter>
  );
}

export default App;

