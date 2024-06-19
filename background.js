browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "group_tabs") {
        fetchTabUrls().then(tabs => {
            const tabUrls = tabs.map(tab => tab.url);
            console.log("Tab URLs retrieved:", tabUrls);

            fetch('http://127.0.0.1:5000/predict_topic', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ urls: tabUrls })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(topics => {
                console.log("Topics received:", topics);

                const groupedTabs = {};

                // Group tabs by their assigned topics
                for (let i = 0; i < tabs.length; i++) {
                    const tab = tabs[i];
                    const topicIndex = Number(topics[i]?.topic) || 25; // Default to topic number 25 if topics[i] is undefined

                    if (!groupedTabs[topicIndex]) {
                        groupedTabs[topicIndex] = [];
                    }
                    groupedTabs[topicIndex].push(tab);
                }

                // Create new windows for each topic and move tabs
                const windowPromises = [];
                let windowsCreated = 0;

                Object.entries(groupedTabs).forEach(([topicIndex, tabGroup]) => {
                    // Collect URLs and IDs of the tabs to move
                    const tabUrlsToMove = tabGroup.map(tab => tab.url);
                    const tabIdsToRemove = tabGroup.map(tab => tab.id);

                    // Create a new window with the grouped tabs
                    windowPromises.push(new Promise((resolve) => {
                        browser.windows.create({ url: tabUrlsToMove, focused: true }).then((newWindow) => {
                            // Maximize the new window
                            browser.windows.update(newWindow.id, { state: 'maximized' }).then(() => {
                                // Remove the original tabs after moving
                                browser.tabs.remove(tabIdsToRemove).then(() => {
                                    windowsCreated++;
                                    resolve();
                                });
                            });
                        });
                    }));
                });

                // Wait for all windows to be created, tabs moved, and original tabs removed
                Promise.all(windowPromises)
                    .then(() => {
                        console.log("Tabs moved to respective windows successfully and original tabs removed.");
                        sendResponse({ success: true, windowsCreated: windowsCreated });
                    })
                    .catch(error => {
                        console.error('Error moving tabs to windows or removing original tabs:', error);
                        sendResponse({ success: false });
                    });
            })
            .catch(error => {
                console.error('Error fetching topics:', error);
                // Handle case where topics are undefined or fetch failed
                // Default to topic number 25 for all tabs
                const topicIndex = 25;
                const groupedTabs = { [topicIndex]: tabs };

                const windowPromises = tabs.map(tab => {
                    const tabUrlsToMove = [tab.url];
                    const tabIdsToRemove = [tab.id];

                    return new Promise((resolve) => {
                        browser.windows.create({ url: tabUrlsToMove, focused: true }).then((newWindow) => {
                            browser.windows.update(newWindow.id, { state: 'maximized' }).then(() => {
                                browser.tabs.remove(tabIdsToRemove).then(() => {
                                    resolve();
                                });
                            });
                        });
                    });
                });

                Promise.all(windowPromises)
                    .then(() => {
                        console.log("Tabs moved to respective windows successfully and original tabs removed.");
                        sendResponse({ success: true, windowsCreated: tabs.length });
                    })
                    .catch(error => {
                        console.error('Error moving tabs to windows or removing original tabs:', error);
                        sendResponse({ success: false });
                    });
            });
        });

        // Return true to indicate that the response will be sent asynchronously
        return true;
    }
});

async function fetchTabUrls() {
    const tabs = await browser.tabs.query({});
    return tabs;
}
