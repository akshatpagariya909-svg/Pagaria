// Visitor counting with GoatCounter (free, no cookies, no consent banner).
// To switch it on: create a site at https://www.goatcounter.com and put its code between the quotes.
// Leave it empty and nothing is sent anywhere.
(function () {
  var CODE = 'akshatpagaria';
  if (!CODE) return;
  window.goatcounter = { endpoint: 'https://' + CODE + '.goatcounter.com/count' };
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://gc.zgo.at/count.js';
  document.head.appendChild(s);
})();
