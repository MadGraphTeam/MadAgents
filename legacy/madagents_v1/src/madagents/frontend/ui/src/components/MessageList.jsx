import React, { memo } from "react";
import { getRecipientDisplayName, stripControlChars } from "../lib/formatters";
import ReplyAccordion from "./ReplyAccordion";
import OrchestratorReasoningBlock from "./OrchestratorReasoningBlock";
import MarkdownBubble from "./MarkdownBubble";
import AgentOpGroup from "./AgentOpGroup";
import {
  PlanCard,
  PlanUpdatesCard,
  renderPlanLabel,
  renderPlanUpdateLabel,
} from "./PlanCard";

/**
 * Scrollable list of messages with inline plan and trace rendering.
 */
const MessageList = memo(function MessageList({
  processedMessages,
  theme,
  loading,
  error,
  scrollContainerRef,
  isHistoryLoading,
  selectedThreadId,
  rewindStatus,
  rewindEditIndex,
  rewindError,
  isRewinding,
  rewindDisabled,
  onStartRewind,
  onCancelRewind,
  onConfirmRewind,
  rewindTextRef,
}) {
  const emptyStateText =
    selectedThreadId === "-1"
      ? "Start the conversation below…"
      : isHistoryLoading
        ? "Loading..."
        : "";
  return (
    <>
      <div
        ref={scrollContainerRef}
        style={{
          flex: 1,
          minHeight: 0,
          padding: "1rem",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "0.75rem",
        }}
      >
        {processedMessages.length === 0 && emptyStateText && (
          <div style={{ opacity: 0.6 }}>{emptyStateText}</div>
        )}

        {processedMessages.map((item, idx) => {
          if (item.type === "agentOpGroup") {
            const groupOrchestratorContent = stripControlChars(
              item.orchestratorContent || ""
            );
            return (
              <React.Fragment key={`agent-group-${idx}`}>
                {groupOrchestratorContent.trim() && (
                  <MarkdownBubble isUser={false} theme={theme}>
                    {groupOrchestratorContent}
                  </MarkdownBubble>
                )}
                <AgentOpGroup group={item} theme={theme} />
              </React.Fragment>
            );
          }

          if (item.type === "orchestratorUpdate") {
            const om = item.message;
            const omRaw =
              typeof om.content === "string"
                ? om.content
                : om.content == null
                  ? ""
                  : JSON.stringify(om.content, null, 2);
            const omText = stripControlChars(omRaw);
            const omAdd = om.add_content || {};
            const omReasoning = stripControlChars(omAdd.reasoning || "");
            return (
              <div
                key={`orch-update-${idx}`}
                style={{
                  alignSelf: "flex-start",
                  maxWidth: "80%",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.15rem",
                  boxSizing: "border-box",
                }}
              >
                <OrchestratorReasoningBlock
                  reasoning={omReasoning}
                  futureNote=""
                  theme={theme}
                />
                {omText.trim() && (
                  <MarkdownBubble
                    isUser={false}
                    theme={theme}
                    showCopy={true}
                    copyText={omText}
                  >
                    {omText}
                  </MarkdownBubble>
                )}
                {(item.inlineMessages || []).map((msg, inlineIdx) => {
                  const inlineAddContent = msg.add_content || {};
                  const inlinePlan = inlineAddContent.plan;
                  const inlinePlanUpdateSteps = Array.isArray(
                    inlineAddContent.plan_update_steps
                  )
                    ? inlineAddContent.plan_update_steps
                    : [];
                  if (inlinePlanUpdateSteps.length > 0) {
                    return (
                      <ReplyAccordion
                        key={`inline-${inlineIdx}`}
                        theme={theme}
                        defaultOpen={true}
                        label={renderPlanUpdateLabel(inlinePlanUpdateSteps, theme, inlinePlan)}
                      >
                        <PlanUpdatesCard
                          steps={inlinePlanUpdateSteps}
                          theme={theme}
                          showStatusIcons={false}
                        />
                      </ReplyAccordion>
                    );
                  }
                  if (inlinePlan && Array.isArray(inlinePlan.steps)) {
                    return (
                      <ReplyAccordion
                        key={`inline-${inlineIdx}`}
                        theme={theme}
                        defaultOpen={false}
                        label={renderPlanLabel(inlinePlan, theme)}
                      >
                        <PlanCard plan={inlinePlan} theme={theme} />
                      </ReplyAccordion>
                    );
                  }
                  return null;
                })}
              </div>
            );
          }

          if (item.type === "parallelAgentOpGroup") {
            const parallelOrchestratorContent = (() => {
              const om = item.orchestratorMessage;
              if (!om) return "";
              const raw = typeof om.content === "string" ? om.content : "";
              return stripControlChars(raw);
            })();
            return (
              <React.Fragment key={`parallel-group-${idx}`}>
                {parallelOrchestratorContent.trim() && (
                  <MarkdownBubble isUser={false} theme={theme}>
                    {parallelOrchestratorContent}
                  </MarkdownBubble>
                )}
                {(item.subGroups || []).map((subGroup, subIdx) => (
                  <AgentOpGroup
                    key={`parallel-sub-${idx}-${subIdx}`}
                    group={subGroup}
                    theme={theme}
                  />
                ))}
              </React.Fragment>
            );
          }

          const m = item.message;
          const isUser = m.name === "user";
          const isOrchestrator = m.name === "orchestrator";
          const msgInstanceId = m.add_content?.instance_id;
          const displayName = getRecipientDisplayName(m.name || "assistant", msgInstanceId);

          const addContent = m.add_content || {};
          const plan = addContent.plan;
          const hasPlan = Boolean(plan && Array.isArray(plan.steps));
          const planUpdateSteps = Array.isArray(addContent.plan_update_steps)
            ? addContent.plan_update_steps
            : [];
          const rawContentText =
            typeof m.content === "string"
              ? m.content
              : m.content == null
                ? ""
                : JSON.stringify(m.content, null, 2);
          const contentText = stripControlChars(rawContentText);
          const hasContent = contentText.trim().length > 0;
          const orchestratorRecipient = isOrchestrator ? (addContent.recipient || "") : "";
          const orchestratorRecipientDisplay = getRecipientDisplayName(
            orchestratorRecipient
          );
          const orchestratorReasoning = isOrchestrator
            ? stripControlChars(addContent.reasoning || "")
            : "";
          const orchestratorEffort = isOrchestrator ? addContent.reasoning_effort : "";
          const orchestratorFutureNote =
            isOrchestrator && typeof addContent.future_note === "string"
              ? stripControlChars(addContent.future_note)
              : "";
          const orchestratorInstruction = stripControlChars(
            isOrchestrator && addContent.message ? addContent.message : ""
          );
          // User-facing text from the orchestrator (shown outside the accordion)
          const orchestratorContentText =
            isOrchestrator && addContent.message ? contentText : "";
          // For user-directed messages (no dispatch), show content directly
          const orchestratorMessage = orchestratorInstruction || contentText;
          const isPlannerReply =
            m.name === "planner" || m.name === "plan_updater";
          const showPlanUpdates =
            m.name === "plan_updater" && planUpdateSteps.length > 0;

          const isOrchestratorToUser =
            isOrchestrator &&
            (orchestratorRecipient === "user" ||
              orchestratorRecipient === "end_user" ||
              orchestratorRecipient === "");

          // User-facing: no explicit recipient in add_content (recipient is "")
          // Legacy messages may have explicit recipient "user" or "end_user"
          const isImplicitOrchestratorToUser =
            isOrchestrator && isOrchestratorToUser && !orchestratorRecipient;
          const orchestratorFoldable = isOrchestrator && !isOrchestratorToUser;
          const showOrchestratorEffort =
            isOrchestrator && !isOrchestratorToUser && Boolean(orchestratorEffort);
          const shouldAccordionWrap = !isUser && !isOrchestrator;
          const effectiveRewindStatus = rewindStatus || "pending";
          const isRewindLoading = effectiveRewindStatus === "pending";
          const isRewindReady = effectiveRewindStatus === "ready";
          const isRewindError = effectiveRewindStatus === "error";
          const canRewind = isUser && isRewindReady && Boolean(m.can_rewind_before);
          const showRewindButton =
            isUser &&
            typeof m.message_index === "number" &&
            (isRewindLoading || isRewindReady || isRewindError);
          let rewindTooltip = "Rewind from this message isn't available.";
          if (isRewindLoading) {
            rewindTooltip = "Checking rewind compatibility…";
          } else if (canRewind) {
            rewindTooltip = "Rewind the conversation from this message.";
          } else if (isRewindError) {
            rewindTooltip = "Rewind compatibility is unavailable.";
          }
          const isEditingRewind =
            isUser &&
            typeof m.message_index === "number" &&
            rewindEditIndex === m.message_index;

          const showMessageCopy = true;
          return (
            <div
              key={idx}
              style={{
                alignSelf: isUser ? "flex-end" : "flex-start",
                maxWidth: "80%",
                width: isEditingRewind ? "100%" : "auto",
                display: "flex",
                flexDirection: "column",
                gap: (isOrchestrator && !isImplicitOrchestratorToUser) ? "0.05rem" : "0.15rem",
                boxSizing: "border-box",
              }}
            >
              {!isUser && !isOrchestrator && (
                <div
                  style={{
                    fontSize: "0.75rem",
                    opacity: 0.7,
                    marginLeft: "0.25rem",
                    marginBottom: "0.1rem",
                  }}
                >
                  {displayName}
                </div>
              )}

              {isOrchestrator && !isImplicitOrchestratorToUser && (
                <div
                  style={{
                    fontSize: "0.8rem",
                    opacity: 0.75,
                    marginLeft: "0.25rem",
                    marginBottom: "0.0rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.35rem",
                  }}
                >
                  <span style={{ fontWeight: 500 }}>
                    {getRecipientDisplayName("orchestrator")}
                  </span>
                  <span style={{ opacity: 0.6 }}>→</span>
                  <span>{orchestratorRecipientDisplay}</span>
                  {showOrchestratorEffort && (
                    <span style={{ fontSize: "0.7rem", opacity: 0.6 }}>
                      effort: {orchestratorEffort}
                    </span>
                  )}
                </div>
              )}

              {isEditingRewind ? (
                <div
                  style={{
                    background: theme.userBubbleBg,
                    color: theme.userBubbleText,
                    borderRadius: "1rem 1rem 0.25rem 1rem",
                    padding: "0.75rem 1rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.6rem",
                    width: "100%",
                    boxSizing: "border-box",
                  }}
                >
                  <div style={{ fontSize: "0.8rem", opacity: 0.85 }}>
                    Edit message for rewind
                  </div>
                  <textarea
                    defaultValue={contentText}
                    ref={rewindTextRef}
                    rows={14}
                    wrap="off"
                    style={{
                      width: "100%",
                      borderRadius: "0.5rem",
                      border: `1px solid ${theme.border}`,
                      padding: "0.5rem 0.6rem",
                      fontSize: "0.9rem",
                      fontFamily: "inherit",
                      color: theme.userBubbleText,
                      background: "rgba(255,255,255,0.08)",
                      outline: "none",
                      overflowX: "auto",
                      overflowY: "auto",
                      maxHeight: "240px",
                      resize: "none",
                      boxSizing: "border-box",
                    }}
                  />
                  {rewindError && (
                    <div style={{ fontSize: "0.75rem", opacity: 0.85 }}>
                      {rewindError}
                    </div>
                  )}
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button
                      type="button"
                      onClick={onCancelRewind}
                      disabled={isRewinding}
                      style={{
                        border: `1px solid ${theme.border}`,
                        background: "transparent",
                        color: theme.userBubbleText,
                        borderRadius: "999px",
                        padding: "0.35rem 0.75rem",
                        cursor: isRewinding ? "default" : "pointer",
                        opacity: isRewinding ? 0.6 : 1,
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => onConfirmRewind(m)}
                      disabled={isRewinding || rewindDisabled}
                      style={{
                        border: "none",
                        background: theme.accentDark,
                        color: "white",
                        borderRadius: "999px",
                        padding: "0.35rem 0.85rem",
                        cursor:
                          isRewinding || rewindDisabled ? "default" : "pointer",
                        opacity: isRewinding || rewindDisabled ? 0.6 : 1,
                      }}
                    >
                      {isRewinding ? "Rewinding..." : "Rewind & run"}
                    </button>
                  </div>
                </div>
              ) : isOrchestrator ? (
                orchestratorFoldable ? (
                  <>
                    {orchestratorContentText.trim() && (
                      <MarkdownBubble isUser={false} theme={theme}>
                        {orchestratorContentText}
                      </MarkdownBubble>
                    )}
                    <ReplyAccordion theme={theme} defaultOpen={false} label="Instruction">
                      <OrchestratorReasoningBlock
                        reasoning={orchestratorReasoning}
                        futureNote={orchestratorFutureNote}
                        theme={theme}
                      />

                      <MarkdownBubble isUser={false} theme={theme}>
                        {orchestratorInstruction}
                      </MarkdownBubble>
                    </ReplyAccordion>
                  </>
                ) : (
                  <>
                    <OrchestratorReasoningBlock
                      reasoning={orchestratorReasoning}
                      futureNote={orchestratorFutureNote}
                      theme={theme}
                    />

                    <MarkdownBubble
                      isUser={false}
                      theme={theme}
                      showCopy={isOrchestratorToUser}
                      copyText={orchestratorMessage}
                    >
                      {orchestratorMessage}
                    </MarkdownBubble>
                  </>
                )
              ) : (
                <>
                  {showPlanUpdates && (
                    <PlanUpdatesCard steps={planUpdateSteps} theme={theme} />
                  )}
                  {hasPlan && (
                    <ReplyAccordion
                      theme={theme}
                      defaultOpen={!showPlanUpdates}
                      label={
                        showPlanUpdates
                          ? renderPlanLabel(plan, theme, "Full plan")
                          : renderPlanLabel(plan, theme)
                      }
                    >
                      <PlanCard plan={plan} theme={theme} />
                    </ReplyAccordion>
                  )}
                  {hasContent && !showPlanUpdates &&
                    (shouldAccordionWrap ? (
                      <ReplyAccordion theme={theme} defaultOpen={isPlannerReply}>
                        <MarkdownBubble
                          isUser={false}
                          theme={theme}
                          showCopy={showMessageCopy}
                          copyText={contentText}
                        >
                          {contentText}
                        </MarkdownBubble>
                      </ReplyAccordion>
                    ) : (
                      <MarkdownBubble
                        isUser={isUser}
                        theme={theme}
                        showCopy={showMessageCopy}
                        copyText={contentText}
                        showRewind={showRewindButton}
                        rewindDisabled={rewindDisabled || !canRewind}
                        rewindLoading={isRewindLoading}
                        rewindTooltip={rewindTooltip}
                        onRewind={() => onStartRewind(m)}
                      >
                        {contentText}
                      </MarkdownBubble>
                    ))}
                </>
              )}
            </div>
          );
        })}

        {loading && (
          <div style={{ alignSelf: "flex-start", fontSize: "0.95rem", opacity: 0.7 }}>
            Thinking…
          </div>
        )}
      </div>

      {error && (
        <div
          style={{
            color: theme.errorText,
            fontSize: "0.9rem",
            padding: "0 1rem 0.5rem",
          }}
        >
          {error}
        </div>
      )}
    </>
  );
});

export default MessageList;
