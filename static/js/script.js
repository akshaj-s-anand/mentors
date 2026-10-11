const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Hero slider (home page only): headline N, sub-line N and dot N always move together
const heroSlider = document.getElementById('heroSlider');
if (heroSlider) {
    const headlines = heroSlider.querySelectorAll('.headline-rotator > .primary-h1');
    const sublines = heroSlider.querySelectorAll('.subline-rotator > .primary-p');
    const dots = heroSlider.querySelectorAll('.hero-dots button');
    const interval = Number(heroSlider.dataset.interval) || 4500;
    heroSlider.style.setProperty('--slide-interval', `${interval}ms`);

    let current = 0;
    let timer = null;
    let remaining = interval;
    let startedAt = 0;
    const pauseReasons = new Set();

    const schedule = () => {
        clearTimeout(timer);
        if (pauseReasons.size) return;
        startedAt = performance.now();
        timer = setTimeout(() => goTo((current + 1) % headlines.length), remaining);
    };

    const setSlide = (list, index, previous) => {
        list.forEach(el => el.classList.remove('leaving'));
        if (previous !== index) {
            list[previous].classList.remove('visible');
            list[previous].classList.add('leaving');
            list[previous].setAttribute('aria-hidden', 'true');
        }
        list[index].classList.add('visible');
        list[index].removeAttribute('aria-hidden');
    };

    function goTo(index) {
        const previous = current;
        current = index;
        setSlide(headlines, index, previous);
        setSlide(sublines, index, previous);
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
            if (i === index) dot.setAttribute('aria-current', 'true');
            else dot.removeAttribute('aria-current');
        });
        // restart the progress fill even when the same dot is re-selected
        const activeDot = dots[index];
        if (activeDot) {
            activeDot.classList.remove('active');
            void activeDot.offsetWidth;
            activeDot.classList.add('active');
        }
        remaining = interval;
        schedule();
    }

    const pause = reason => {
        if (!pauseReasons.size) {
            clearTimeout(timer);
            remaining = Math.max(0, remaining - (performance.now() - startedAt));
            heroSlider.classList.add('is-paused');
        }
        pauseReasons.add(reason);
    };

    const resume = reason => {
        pauseReasons.delete(reason);
        if (!pauseReasons.size) {
            heroSlider.classList.remove('is-paused');
            schedule();
        }
    };

    dots.forEach((dot, i) => dot.addEventListener('click', () => goTo(i)));

    // hold the slide while the visitor is reading or interacting with it
    heroSlider.addEventListener('mouseenter', () => pause('hover'));
    heroSlider.addEventListener('mouseleave', () => resume('hover'));
    heroSlider.addEventListener('focusin', () => pause('focus'));
    heroSlider.addEventListener('focusout', () => resume('focus'));
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) pause('hidden');
        else resume('hidden');
    });

    schedule();
}

// this script is loaded at the end of <body>, so the DOM is already parsed
(() => {
    // Clickable cards
    document.querySelectorAll('[data-link]').forEach(el => {
        el.addEventListener('click', () => {
            window.location.href = el.getAttribute('data-link');
        });
    });

    // Glass navbar gets denser once the page scrolls
    const nav = document.getElementById('siteNav');
    if (nav) {
        const onScroll = () => nav.classList.toggle('is-scrolled', window.scrollY > 10);
        onScroll();
        window.addEventListener('scroll', onScroll, { passive: true });

        // Close the mobile menu after picking a link
        const collapseEl = nav.querySelector('.navbar-collapse');
        nav.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (collapseEl.classList.contains('show') && window.bootstrap) {
                    bootstrap.Collapse.getOrCreateInstance(collapseEl).hide();
                }
            });
        });
    }

})();

// Scroll reveal: elements marked data-reveal, plus common blocks automatically.
// Called again for content swapped in by AJAX.
const revealObserver = (prefersReducedMotion || !('IntersectionObserver' in window))
    ? null
    : new IntersectionObserver(entries => {
        // stagger siblings that enter together
        let batchIndex = 0;
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            el.style.setProperty('--reveal-delay', `${Math.min(batchIndex, 5) * 0.08}s`);
            batchIndex += 1;
            el.classList.add('is-revealed');
            el.addEventListener('transitionend', () => {
                el.classList.add('reveal-done');
                el.style.removeProperty('--reveal-delay');
            }, { once: true });
            revealObserver.unobserve(el);
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

function initReveal(root) {
    const autoTargets = '.page .card, .page .project-grid, .page .about-image, .page .glass-panel, .page .section-title';
    root.querySelectorAll(autoTargets).forEach(el => {
        // carousel slides are animated by the carousel itself
        if (!el.closest('.carousel') && !el.closest('[data-reveal]')) el.setAttribute('data-reveal', '');
    });

    root.querySelectorAll('[data-reveal]:not(.is-revealed)').forEach(el => {
        if (revealObserver) revealObserver.observe(el);
        else el.classList.add('is-revealed', 'reveal-done');
    });
}

initReveal(document);

// Infinite scroll & live filtering for list pages ([data-ajax-list]).
// The "Load more" link and the filter form are real URLs, so everything still works without JS.
(() => {
    const list = document.querySelector('[data-ajax-list]');
    if (!list || !window.fetch || !window.history.pushState) return;

    const results = list.querySelector('[data-ajax-results]');
    const form = list.querySelector('[data-ajax-filter]');
    const status = list.querySelector('[data-ajax-status]');
    const canAutoLoad = 'IntersectionObserver' in window;
    let generation = 0; // bumped on every filter change, so a late "load more" can't mix in old results
    let loadingMore = false;

    const fetchFragment = url => fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
    }).then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text();
    });

    const parse = html => {
        const template = document.createElement('template');
        template.innerHTML = html;
        return template.content;
    };

    const withoutPage = url => {
        const parsed = new URL(url, location.href);
        parsed.searchParams.delete('page');
        return parsed.pathname + parsed.search;
    };

    const announce = () => {
        const meta = results.querySelector('.results-meta');
        if (status && meta) status.textContent = meta.textContent.replace(/\s+/g, ' ').trim();
    };

    // start fetching well before the footer is on screen, so cards are usually ready in time
    const observer = canAutoLoad
        ? new IntersectionObserver(entries => {
            if (entries.some(entry => entry.isIntersecting)) loadMore();
        }, { rootMargin: '0px 0px 600px 0px' })
        : null;

    function watchFooter() {
        const footer = results.querySelector('[data-load-more]');
        if (!footer) return;
        // with auto-loading the button is only shown again if a load fails
        footer.classList.toggle('is-auto', canAutoLoad);
        if (observer) {
            observer.disconnect();
            if (footer.dataset.nextUrl) {
                observer.observe(footer);
                // a fast jump (End key, flick) can skip past the trigger entirely;
                // reaching the site footer means we're past the cards, so load then too
                const siteFooter = document.querySelector('.site-footer');
                if (siteFooter) observer.observe(siteFooter);
            }
        }
    }

    async function loadMore() {
        const footer = results.querySelector('[data-load-more]');
        const next = footer && footer.dataset.nextUrl;
        if (!next || loadingMore) return;

        loadingMore = true;
        const loadGeneration = generation;
        const url = new URL(next, location.href).href;
        footer.classList.remove('has-error');
        footer.classList.add('is-loading');
        try {
            const fragment = parse(await fetchFragment(url));
            if (loadGeneration !== generation) return;
            const grid = results.querySelector('[data-card-grid]');
            grid.append(...fragment.querySelector('[data-card-grid]').children);
            footer.replaceWith(fragment.querySelector('[data-load-more]'));
            initReveal(grid);
            // remember how far we got: reload / Back renders the same cards server-side
            history.replaceState(history.state, '', url);
            announce();
            watchFooter();
        } catch (error) {
            if (loadGeneration === generation) {
                footer.classList.remove('is-loading');
                footer.classList.add('has-error');
                // stop retrying automatically; the visitor can press "Load more"
                if (observer) observer.disconnect();
            }
        } finally {
            loadingMore = false;
        }
    }

    // keep the selects in step with the URL (e.g. after Back/Forward)
    const syncForm = url => {
        if (!form) return;
        const params = new URL(url, location.href).searchParams;
        form.querySelectorAll('select[name], input[name]').forEach(field => {
            // don't overwrite what the visitor is still typing
            if (field !== document.activeElement) field.value = params.get(field.name) || '';
        });
    };

    const scrollToResults = () => {
        const navOffset = 110;
        const top = results.getBoundingClientRect().top + window.scrollY - navOffset;
        if (window.scrollY > top) {
            window.scrollTo({ top, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
        }
    };

    // swap in the first page of a new filter selection
    async function replaceResults(url, { push = true } = {}) {
        const loadGeneration = ++generation;
        if (observer) observer.disconnect();
        results.classList.add('is-loading');
        results.setAttribute('aria-busy', 'true');
        try {
            const html = await fetchFragment(url);
            if (loadGeneration !== generation) return;
            results.innerHTML = html;
            if (push) history.pushState({ ajaxList: true }, '', url);
            else history.replaceState({ ajaxList: true }, '', url);
            syncForm(url);
            initReveal(results);
            announce();
            watchFooter();
            scrollToResults();
        } catch (error) {
            // anything unexpected: fall back to a normal page load
            if (loadGeneration === generation) window.location.href = url;
        } finally {
            if (loadGeneration === generation) {
                results.classList.remove('is-loading');
                results.removeAttribute('aria-busy');
            }
        }
    }

    results.addEventListener('click', event => {
        const link = event.target.closest('.load-more-btn, a[data-ajax-link]');
        // let Ctrl/Cmd/Shift/middle clicks open new tabs as usual
        if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        if (link.classList.contains('load-more-btn')) loadMore();
        else replaceResults(withoutPage(link.href));
    });

    if (form) {
        const formUrl = () => {
            const params = new URLSearchParams();
            new FormData(form).forEach((value, key) => { if (value) params.append(key, value); });
            const query = params.toString();
            return location.pathname + (query ? `?${query}` : '');
        };
        // skip requests that wouldn't change anything (e.g. 'change' firing on blur after typing)
        const applyFilters = ({ push = true } = {}) => {
            const url = formUrl();
            if (url !== withoutPage(location.href)) replaceResults(url, { push });
        };
        form.addEventListener('submit', event => {
            event.preventDefault();
            applyFilters();
        });
        // filters apply as soon as they change; the search box waits for a pause in typing
        form.addEventListener('change', event => {
            if (event.target.type !== 'search') applyFilters();
        });
        let typingTimer;
        form.querySelectorAll('input[type="search"]').forEach(input => {
            input.addEventListener('input', () => {
                clearTimeout(typingTimer);
                // typing updates the current history entry instead of adding one per pause
                typingTimer = setTimeout(() => applyFilters({ push: false }), 350);
            });
        });
    }

    history.replaceState({ ajaxList: true }, '', location.href);
    window.addEventListener('popstate', event => {
        // the entry's URL may carry ?page=N from scrolling; restart that filter from the top
        if (event.state && event.state.ajaxList) replaceResults(withoutPage(location.href), { push: false });
    });

    watchFooter();
})();

// Toast messages: dismiss on click, fade out on their own
(() => {
    document.querySelectorAll('[data-toast]').forEach((toast, index) => {
        const dismiss = () => {
            toast.classList.add('is-leaving');
            setTimeout(() => toast.remove(), 400);
        };
        toast.querySelector('[data-toast-close]')?.addEventListener('click', dismiss);
        // errors stay until dismissed; others leave after a few seconds
        if (!toast.classList.contains('toast-error')) setTimeout(dismiss, 6000 + index * 600);
    });
})();

// Forms that need a confirmation first (cancel, decline, delete…)
document.addEventListener('submit', event => {
    const message = event.target.dataset && event.target.dataset.confirm;
    if (message && !window.confirm(message)) event.preventDefault();
});

// Booking form: load free time slots for the chosen date
(() => {
    const form = document.querySelector('[data-booking]');
    const slotList = form && form.querySelector('[data-slot-list]');
    if (!slotList) return;
    const dateInput = form.querySelector('[data-booking-date]');
    let selected = slotList.dataset.selected || '';
    let latest = 0;

    const message = text => {
        slotList.innerHTML = '';
        const p = document.createElement('p');
        p.className = 'slot-hint';
        p.textContent = text;
        slotList.append(p);
    };

    async function loadSlots() {
        if (!dateInput.value) return message('Pick a date to see free times.');
        const requestId = ++latest;
        slotList.classList.add('is-loading');
        try {
            const response = await fetch(`${form.dataset.slotsUrl}?date=${encodeURIComponent(dateInput.value)}`);
            const { slots } = await response.json();
            if (requestId !== latest) return;
            if (!slots.length) return message('No free times that day. Try another date.');
            slotList.innerHTML = '';
            slots.forEach(slot => {
                const label = document.createElement('label');
                label.className = 'slot';
                const input = document.createElement('input');
                input.type = 'radio';
                input.name = 'start_time';
                input.value = slot.value;
                input.required = true;
                input.checked = slot.value === selected;
                input.addEventListener('change', () => { selected = slot.value; });
                const text = document.createElement('span');
                text.textContent = slot.label;
                label.append(input, text);
                slotList.append(label);
            });
        } catch (error) {
            if (requestId === latest) message("Couldn't load times. Check your connection and pick the date again.");
        } finally {
            if (requestId === latest) slotList.classList.remove('is-loading');
        }
    }

    dateInput.addEventListener('change', () => { selected = ''; loadSlots(); });
    if (dateInput.value) loadSlots(); // re-show slots after a validation error
})();

// On-site chat: load the thread, poll for new messages while the page is visible, send replies
(() => {
    const chat = document.querySelector('[data-chat]');
    if (!chat) return;
    const url = chat.dataset.chat;
    const log = chat.querySelector('[data-chat-log]');
    const form = chat.querySelector('[data-chat-form]');
    const textarea = form.querySelector('textarea');
    const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
    let lastId = 0;
    let timer = null;
    let busy = false;
    const shown = new Set(); // a poll and a send can overlap, so track ids rather than trusting order

    const nearBottom = () => log.scrollHeight - log.scrollTop - log.clientHeight < 80;

    const render = (items, { forceScroll = false } = {}) => {
        if (!items.length) return;
        const stick = forceScroll || nearBottom();
        chat.querySelector('[data-chat-empty]')?.remove();
        items.forEach(item => {
            if (shown.has(item.id)) return;
            shown.add(item.id);
            lastId = Math.max(lastId, item.id);
            const bubble = document.createElement('div');
            bubble.className = `chat-msg ${item.mine ? 'is-mine' : ''}`;
            bubble.dataset.id = item.id;
            const body = document.createElement('p');
            body.textContent = item.body; // text only: never inject HTML from messages
            const time = document.createElement('time');
            time.textContent = item.time;
            bubble.append(body, time);
            // keep the thread in id order even if an older message arrives late
            const later = [...log.children].find(el => Number(el.dataset.id) > item.id);
            log.insertBefore(bubble, later || null);
        });
        if (stick) log.scrollTop = log.scrollHeight;
    };

    const setOpen = isOpen => {
        form.hidden = !isOpen;
        chat.querySelector('[data-chat-closed]').hidden = isOpen;
    };

    async function poll() {
        if (busy) return;
        busy = true;
        try {
            const response = await fetch(`${url}?after=${lastId}`, { credentials: 'same-origin' });
            if (response.ok) {
                const data = await response.json();
                setOpen(data.open);
                render(data.messages);
            }
        } catch (error) {
            // offline for a moment: the next poll will catch up
        } finally {
            busy = false;
        }
    }

    const schedule = () => {
        clearInterval(timer);
        if (!document.hidden) timer = setInterval(poll, 4000);
    };

    form.addEventListener('submit', async event => {
        event.preventDefault();
        const text = textarea.value.trim();
        if (!text) return;
        const button = form.querySelector('button');
        button.disabled = true;
        try {
            const response = await fetch(`${url}?after=${lastId}`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'X-CSRFToken': csrf },
                body: new URLSearchParams({ body: text }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Could not send');
            textarea.value = '';
            textarea.style.height = '';
            render(data.messages, { forceScroll: true });
        } catch (error) {
            alert(error.message || 'Could not send your message. Please try again.');
        } finally {
            button.disabled = false;
            textarea.focus();
        }
    });

    // Enter sends, Shift+Enter adds a new line; the box grows with its content
    textarea.addEventListener('keydown', event => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });
    textarea.addEventListener('input', () => {
        textarea.style.height = 'auto';
        textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    });

    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) poll();
        schedule();
    });
    poll();
    schedule();
})();
