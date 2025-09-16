// Inject a dynamic API base and rewrite relative backend calls
(function () {
  try {
    var defaultBase = window.API_BASE_URL || (window.location.protocol + '//' + window.location.host + '/backend');
    window.BASE_URL = defaultBase;

    var origFetch = window.fetch ? window.fetch.bind(window) : null;
    if (origFetch) {
      window.fetch = function (input, init) {
        try {
          if (typeof input === 'string') {
            if (input.startsWith('/backend')) {
              input = defaultBase + input.replace(/^\/backend/, '');
            } else if (input.startsWith('backend')) {
              input = defaultBase + input.replace(/^backend/, '');
            }
          } else if (input && input.url && typeof input.url === 'string') {
            if (input.url.startsWith('/backend')) {
              input = new Request(defaultBase + input.url.replace(/^\/backend/, ''), input);
            }
          }
        } catch (e) {}
        return origFetch(input, init);
      };
    }
  } catch (e) {
    console.log('[api-base] init error', e);
  }
})();

