document.addEventListener('DOMContentLoaded', () => {
  const groupTabsButton = document.getElementById('groupTabs');
  const statusDiv = document.getElementById('status');

  groupTabsButton.addEventListener('click', () => {
      statusDiv.innerHTML = 'Grouping tabs...';
      
      chrome.runtime.sendMessage({ action: "group_tabs" }, (response) => {
          if (response.success) {
              statusDiv.innerHTML = `<span>Grouping done!</span> Number of windows created: ${response.windowsCreated}`;
          } else {
              statusDiv.innerHTML = '<span>Error:</span> Could not group tabs.';
          }
      });
  });
});
