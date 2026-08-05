/* Small shared UI helpers - opt-in, no dependency on any specific page's JS */

/**
 * Animates a numeric counter element from 0 to its own text content.
 * Applied automatically to every .stat-value on the page (see DOMContentLoaded below).
 */
function animateCounter(el, duration = 900) {
    const target = parseFloat((el.textContent || '0').replace(/[^\d.-]/g, ''));
    if (isNaN(target)) return;

    const suffix = (el.textContent || '').replace(/^[\d.,\s-]*/, '');
    const start = performance.now();

    function step(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(target * eased);
        el.textContent = value + suffix;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.stat-value').forEach(el => animateCounter(el));
});

/**
 * Thin wrapper around the SweetAlert2 toast API (already loaded globally via CDN in base.html).
 * Usage: toast('تم الحفظ بنجاح', 'success')
 */
function toast(message, type = 'success') {
    if (typeof Swal === 'undefined') return;
    Swal.mixin({
        toast: true,
        position: 'top-start',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
    }).fire({ icon: type, title: message });
}
