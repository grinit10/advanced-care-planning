with open('useVoiceAgent.ts', 'r') as f:
    content = f.read()

# Add planSummary to return
content = content.replace(
    "    preferences,\n    roomId,\n    connect,",
    "    preferences,\n    planSummary,\n    roomId,\n    connect,"
)

# Add fetchPlanSummary to startPolling
old = (
    "    // Poll transcript + preferences every 1 second for live updates\n"
    "    pollRef.current = setInterval(() => {\n"
    "      fetchTranscript(currentRoomId);\n"
    "      fetchPreferences(currentRoomId);\n"
    "    }, 1000);\n"
    "    // Also fetch immediately\n"
    "    fetchTranscript(currentRoomId);\n"
    "    fetchPreferences(currentRoomId);\n"
    "  }, [fetchTranscript, fetchPreferences]);"
)
new = (
    "    // Poll plan + transcript + preferences every 1 second for live updates\n"
    "    pollRef.current = setInterval(() => {\n"
    "      fetchPlanSummary(currentRoomId);\n"
    "      fetchTranscript(currentRoomId);\n"
    "      fetchPreferences(currentRoomId);\n"
    "    }, 1000);\n"
    "    // Also fetch immediately\n"
    "    fetchPlanSummary(currentRoomId);\n"
    "    fetchTranscript(currentRoomId);\n"
    "    fetchPreferences(currentRoomId);\n"
    "  }, [fetchPlanSummary, fetchTranscript, fetchPreferences]);"
)
content = content.replace(old, new)

with open('useVoiceAgent.ts', 'w') as f:
    f.write(content)
print('Fixed')
