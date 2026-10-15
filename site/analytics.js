// Visitor counting with GoatCounter (free, no cookies, no consent banner).
// To switch it off, empty the quotes after CODE: nothing is then sent anywhere.
(function () {
  var CODE = 'akshatpagaria';
  if (!CODE) return;
  window.goatcounter = { endpoint: 'https://' + CODE + '.goatcounter.com/count' };
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://gc.zgo.at/count.js';
  document.head.appendChild(s);

  // The wall opens a building (or book) without loading a new page: only the #address changes.
  // Count each one as an event, so the daily visits number stays visits and nothing else.
  var last = '';
  function countOpened() {
    var id = '';
    try { id = decodeURIComponent((location.hash || '').slice(1)); } catch (e) { return; }
    if (!id) { last = ''; return; }
    if (id === last) return;
    last = id;
    var isBook = id.indexOf('book:') === 0, key = isBook ? id.slice(5) : id;
    var list = (isBook ? window.BOOKS : window.BUILDINGS) || [], item = null;
    for (var i = 0; i < list.length; i++) if (list[i].id === key) { item = list[i]; break; }
    if (!item) return;  // not a building or book (a filter, say)
    var tries = 0;
    (function send() {
      if (window.goatcounter && window.goatcounter.count) {
        window.goatcounter.count({ path: (isBook ? 'book/' : 'building/') + key, title: item.name || item.title || key, event: true });
      } else if (tries++ < 20) setTimeout(send, 500);
    })();
  }
  window.addEventListener('hashchange', countOpened);
  window.addEventListener('load', countOpened);
})();
