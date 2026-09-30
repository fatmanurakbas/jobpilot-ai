# JobPilot Browser Agent

This small Windows-host process opens the real application site in a visible Chromium window. The FastAPI service stays in Docker. The agent binds only to `127.0.0.1:8765` and accepts requests only from the local Vite origins configured in the script.

## Start it

Install Playwright in the Python environment on the Windows host, then install Chromium:

```powershell
py -m pip install playwright
py -m playwright install chromium
py desktop_agent\jobpilot_browser_agent.py
```

Keep the terminal running. In JobPilot, prepare and verify the form, then choose **Review in Browser**. The visible browser opens with the resolved answers and uploaded package files, verifies the fields again, and leaves the page open. JobPilot does not click Submit in this mode. You may submit manually on the destination website.

The first launch creates `desktop_agent/browser-profile` for the browser session. Sign in to the destination website in that visible window if needed. This local browser profile stays on this computer.
