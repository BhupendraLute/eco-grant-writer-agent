"use client";

import { useState, useCallback } from "react";
import { useAgent } from "@/hooks/useAgent";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatPanel from "@/components/ChatPanel";
import ChatInput from "@/components/ChatInput";
import TemplateCards from "@/components/TemplateCards";
import SecurityModal from "@/components/SecurityModal";
import DocumentPreview from "@/components/DocumentPreview";

export default function Home() {
  const {
    messages,
    state,
    phase,
    loading,
    interruptId,
    send,
    reset,
  } = useAgent();

  const [showSecurityModal, setShowSecurityModal] = useState(false);
  const [securityMessage, setSecurityMessage] = useState("");

  // Check if we need to show the security modal
  // When an interruptId is set, the last message from the assistant
  // is the security warning.
  const handleSend = useCallback(
    async (message: string, displayText?: string) => {
      await send(message, displayText);
    },
    [send]
  );

  const handleOptionClick = useCallback(
    (value: string, displayText: string) => {
      handleSend(value, displayText);
    },
    [handleSend]
  );

  const handleTemplateSelect = useCallback(
    (prompt: string) => {
      handleSend(prompt);
    },
    [handleSend]
  );

  // Check if we should show the security modal based on interruptId
  const shouldShowSecurityModal =
    interruptId &&
    interruptId !== "compliance_review_choice" &&
    !showSecurityModal;

  // If there's a security interrupt, show the modal
  if (shouldShowSecurityModal && messages.length > 0) {
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.role === "assistant" && !showSecurityModal) {
      // Set modal state
      setTimeout(() => {
        setSecurityMessage(lastMsg.content);
        setShowSecurityModal(true);
      }, 0);
    }
  }

  const handleSecurityApprove = () => {
    setShowSecurityModal(false);
    send("Approve");
  };

  const handleSecurityReject = () => {
    setShowSecurityModal(false);
    send("Reject");
  };

  const isWelcome = phase === "welcome" && messages.length === 0;
  const showDocPreview = !!state.drafted_proposal;

  return (
    <div className="flex flex-col h-screen">
      {/* Navbar */}
      <Navbar phase={phase} onReset={reset} />

      {/* Main Content */}
      <div className="flex flex-1 pt-[60px] overflow-hidden">
        {/* Sidebar (hidden on welcome) */}
        {!isWelcome && <Sidebar state={state} />}

        {/* Center: Chat or Welcome */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {isWelcome ? (
            <TemplateCards onSelect={handleTemplateSelect} />
          ) : (
            <>
              <ChatPanel
                messages={messages}
                loading={loading}
                onOptionClick={handleOptionClick}
              />
              <ChatInput onSend={(msg) => handleSend(msg)} loading={loading} />
            </>
          )}
        </main>

        {/* Document Preview (shown when proposal is drafted) */}
        {showDocPreview && (
          <DocumentPreview
            proposal={state.drafted_proposal}
            isCompliant={state.is_compliant}
            securityApproved={state.security_approved}
            targetGrant={state.target_grant}
          />
        )}
      </div>

      {/* Security Modal */}
      {showSecurityModal && (
        <SecurityModal
          message={securityMessage}
          onApprove={handleSecurityApprove}
          onReject={handleSecurityReject}
        />
      )}
    </div>
  );
}
