// Proxy Authentication Extension
// This extension handles proxy authentication automatically

function parseProxyUrl(proxyUrl) {
  // Format: socks5://username:password@host:port
  // or: http://username:password@host:port
  const match = proxyUrl.match(/^(socks5|http|https):\/\/(?:([^:]+):([^@]+)@)?([^:]+):(\d+)$/);
  if (match) {
    return {
      protocol: match[1],
      username: match[2] || '',
      password: match[3] || '',
      host: match[4],
      port: match[5]
    };
  }
  return null;
}

// Get proxy credentials from Chrome storage or environment
chrome.webRequest.onAuthRequired.addListener(
  function(details, callback) {
    // Try to get proxy URL from Chrome storage
    chrome.storage.local.get(['proxyUrl'], function(data) {
      if (data.proxyUrl) {
        const proxyInfo = parseProxyUrl(data.proxyUrl);
        if (proxyInfo && proxyInfo.username && proxyInfo.password) {
          callback({
            authCredentials: {
              username: proxyInfo.username,
              password: proxyInfo.password
            }
          });
          return;
        }
      }
      // If no credentials found, cancel the request
      callback({ cancel: true });
    });
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);


