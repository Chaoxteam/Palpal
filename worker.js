// Query local monitoring consent before accessing any tab title or URL.
let sequence = 0;
async function report() {
  const mine = ++sequence;
  try {
    const {token} = await chrome.storage.local.get('token');
    if (!token) return;
    const headers = {'Authorization':'Bearer '+token};
    const response = await fetch('http://127.0.0.1:47831/status',{headers});
    if (!response.ok) return;
    const {epoch} = await response.json();
    if (!epoch || mine !== sequence) return;
    const win = (await chrome.windows.getAll()).find(w => w.focused);
    if (!win) return;
    const [tab] = await chrome.tabs.query({active:true,windowId:win.id});
    if (mine !== sequence) return;
    const url = tab?.url ? new URL(tab.url) : null;
    const web = url && ['http:', 'https:'].includes(url.protocol);
    const browser = /Edg\//.test(navigator.userAgent) ? 'msedge.exe' : 'chrome.exe';
    await fetch('http://127.0.0.1:47831/context',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({epoch,browser,title:web ? (tab.title||'').slice(0,512) : '',domain:web ? url.hostname : '',timestamp:Date.now()})});
  } catch {} // No persistence, retries, logging, or remote fallback.
}
chrome.tabs.onActivated.addListener(report);
chrome.tabs.onUpdated.addListener((id,change,tab)=>{if(tab.active&&(change.title||change.status==='complete')) report();});
chrome.windows.onFocusChanged.addListener(report);
