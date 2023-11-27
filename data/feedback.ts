export function addSuggestion(user: string, suggest: string) {
    if (!process.env.SUGGESTION_WEBHOOK_URL) return;
    fetch(process.env.SUGGESTION_WEBHOOK_URL, {
        method: "post",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            content: `# Suggestion\nBy ${user}:\n\n${suggest}`
        })
    });
}

export function addBugReport(user: string, bugReport: string) {
    if (!process.env.SUGGESTION_WEBHOOK_URL) return;
    fetch(process.env.SUGGESTION_WEBHOOK_URL, {
        method: "post",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            content: `# Bug Report\nBy ${user}:\n\n${bugReport}`
        })
    });
}
