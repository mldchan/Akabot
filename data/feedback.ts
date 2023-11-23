export function addSuggestion(user: string, suggest: string) {
  fetch(
    "https://discord.com/api/webhooks/1177345087156519043/XHB62kitDj70rXahALcQTSn0BvU4RzsUX9AZtoWMFUUldeimFneJPP7pyoN2ArGzOCOK",
    {
      method: "post",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: `# Suggestion\nBy ${user}:\n\n${suggest}`,
      }),
    }
  );
}

export function addBugReport(user: string, bugReport: string) {
  fetch(
    "https://discord.com/api/webhooks/1177345087156519043/XHB62kitDj70rXahALcQTSn0BvU4RzsUX9AZtoWMFUUldeimFneJPP7pyoN2ArGzOCOK",
    {
      method: "post",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: `# Bug Report\nBy ${user}:\n\n${bugReport}`,
      }),
    }
  );
}
