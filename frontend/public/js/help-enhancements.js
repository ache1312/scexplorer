// Enhance Help modals: clickable image zoom + numbered reference styling
document.addEventListener('DOMContentLoaded', function () {
  try {
    // 1) Style numbered references like (1) -> bold red
    document.querySelectorAll('.modal_help-body p').forEach(function (p) {
      // Replace occurrences of (number) with a styled span
      p.innerHTML = p.innerHTML.replace(/\((\d+)\)/g, '<span class="ref-num">($1)</span>');
    });

    // 2) Prepare a reusable lightbox overlay for help images
    var overlay = document.createElement('div');
    overlay.className = 'image-lightbox';
    overlay.style.display = 'none';

    var img = document.createElement('img');
    overlay.appendChild(img);
    document.body.appendChild(overlay);

    // Close overlay on click or ESC
    overlay.addEventListener('click', function () {
      overlay.style.display = 'none';
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') overlay.style.display = 'none';
    });

    // 3) Delegate clicks on images inside help modals to open overlay
    document.addEventListener('click', function (e) {
      var target = e.target;
      if (!target) return;
      if (target.closest && target.closest('.modal_help-body') && target.tagName === 'IMG') {
        img.src = target.getAttribute('src');
        overlay.style.display = 'flex';
      }
    });

    // 4) Add a visual cue for zoomable images
    document.querySelectorAll('.modal_help-body img').forEach(function (image) {
      image.classList.add('zoomable');
    });
  } catch (err) {
    // Fail-safe: do not break the app if something goes wrong
    console.warn('Help enhancements failed to initialize:', err);
  }
});

