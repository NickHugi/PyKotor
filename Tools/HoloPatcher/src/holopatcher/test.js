const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    const htmlFilePath = path.resolve(__dirname, 'template.html');
    const htmlContent = fs.readFileSync(htmlFilePath, 'utf8');

    await page.setContent(htmlContent, { waitUntil: 'domcontentloaded' });

    // Capture console.log messages from the page
    page.on('console', msg => {
        for (let i = 0; i < msg.args().length; ++i) {
            console.log(`${i}: ${msg.args()[i]}`);
        }
    });

    async function resetPage() {
        await page.setContent(htmlContent, { waitUntil: 'domcontentloaded' });
    }

    async function addLogEntry() {
        await page.evaluate(() => {
            appendLogLine('This is a log message', 'INFO');
        });
    }

    async function removeAllLogs() {
        await page.evaluate(() => {
            const logsContainer = document.getElementById('logs').querySelector('tbody');
            while (logsContainer.firstChild) {
                logsContainer.removeChild(logsContainer.firstChild);
            }
            updateExpanderState();
        });
    }

    async function enterContent() {
        const content = await page.evaluate(() => {
            return prompt('Enter content for the main view:');
        });
        if (content !== null) {
            await page.evaluate((content) => {
                document.getElementById('content').innerHTML = content;
                updateExpanderState();
            }, content);
        }
    }

    async function removeAllContent() {
        await page.evaluate(() => {
            document.getElementById('content').innerHTML = '';
            updateExpanderState();
        });
    }

    // Adding buttons to run each test manually
    await page.evaluate(() => {
        const body = document.querySelector('body');
        const testButtons = document.createElement('div');
        testButtons.id = 'test-buttons';
        testButtons.style.position = 'fixed';
        testButtons.style.top = '10px';
        testButtons.style.right = '10px';
        testButtons.style.backgroundColor = '#f9f9f9';
        testButtons.style.border = '1px solid #ccc';
        testButtons.style.padding = '10px';
        testButtons.style.zIndex = '1000';

        testButtons.innerHTML = `
            <button id="add-log-entry">Add Log Entry</button>
            <button id="remove-all-logs">Remove All Logs</button>
            <button id="enter-content">Enter Content</button>
            <button id="remove-all-content">Remove All Content</button>
        `;

        body.appendChild(testButtons);
    });

    // Exposing functions to page context
    await page.exposeFunction('addLogEntry', addLogEntry);
    await page.exposeFunction('removeAllLogs', removeAllLogs);
    await page.exposeFunction('enterContent', enterContent);
    await page.exposeFunction('removeAllContent', removeAllContent);

    // Adding event listeners to buttons
    await page.evaluate(() => {
        document.getElementById('add-log-entry').addEventListener('click', () => {
            window.addLogEntry().catch(console.error);
        });
        document.getElementById('remove-all-logs').addEventListener('click', () => {
            window.removeAllLogs().catch(console.error);
        });
        document.getElementById('enter-content').addEventListener('click', () => {
            window.enterContent().catch(console.error);
        });
        document.getElementById('remove-all-content').addEventListener('click', () => {
            window.removeAllContent().catch(console.error);
        });
    });

    // Open browser and display page for manual testing
})();
