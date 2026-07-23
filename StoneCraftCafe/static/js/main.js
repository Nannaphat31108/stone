(() => {
    "use strict";

    const html = document.documentElement;
    const body = document.body;
    const header = document.getElementById("siteHeader");
    const loader = document.getElementById("siteLoader");
    const navToggle = document.getElementById("navToggle");
    const mainNav = document.getElementById("mainNav");
    const languageSwitch = document.getElementById("languageSwitch");
    const progress = document.getElementById("scrollProgress");
    const backToTop = document.getElementById("backToTop");

    window.addEventListener("load", () => {
        window.setTimeout(() => loader?.classList.add("hidden"), 350);
    });

    const setHeaderState = () => {
        const scrolled = window.scrollY > 30;
        header?.classList.toggle("scrolled", scrolled);
        backToTop?.classList.toggle("visible", window.scrollY > 500);

        if (progress) {
            const height = document.documentElement.scrollHeight - window.innerHeight;
            const percent = height > 0 ? (window.scrollY / height) * 100 : 0;
            progress.style.width = `${percent}%`;
        }
    };

    window.addEventListener("scroll", setHeaderState, { passive: true });
    setHeaderState();

    navToggle?.addEventListener("click", () => {
        const isOpen = body.classList.toggle("nav-open");
        navToggle.setAttribute("aria-expanded", String(isOpen));
    });

    mainNav?.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", () => {
            body.classList.remove("nav-open");
            navToggle?.setAttribute("aria-expanded", "false");
        });
    });

    const setLanguage = (language) => {
        html.dataset.language = language;
        html.lang = language;
        localStorage.setItem("stonecraft-language", language);

        document.querySelectorAll("[data-th][data-en]").forEach(element => {
            const value = element.dataset[language];
            if (value !== undefined) {
                element.innerHTML = value;
            }
        });

        const labels = languageSwitch?.querySelectorAll("span");
        labels?.forEach(label => label.classList.remove("language-active"));

        if (labels?.length >= 3) {
            labels[language === "th" ? 0 : 2].classList.add("language-active");
        }
    };

    const savedLanguage = localStorage.getItem("stonecraft-language") || "th";
    setLanguage(savedLanguage);

    languageSwitch?.addEventListener("click", () => {
        setLanguage(html.dataset.language === "th" ? "en" : "th");
    });

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("show");
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.12,
        rootMargin: "0px 0px -50px 0px"
    });

    document.querySelectorAll(".reveal").forEach(element => observer.observe(element));

    const counterObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;

            const element = entry.target;
            const target = Number(element.dataset.target || 0);
            const duration = 1400;
            const start = performance.now();

            const animate = now => {
                const progressValue = Math.min((now - start) / duration, 1);
                const eased = 1 - Math.pow(1 - progressValue, 3);
                const value = Math.floor(target * eased);
                element.textContent = target >= 1000 ? value.toLocaleString() : String(value);

                if (progressValue < 1) requestAnimationFrame(animate);
                else element.textContent = target.toLocaleString();
            };

            requestAnimationFrame(animate);
            counterObserver.unobserve(element);
        });
    }, { threshold: 0.5 });

    document.querySelectorAll(".counter").forEach(counter => counterObserver.observe(counter));

    document.querySelectorAll(".menu-filter").forEach(button => {
        button.addEventListener("click", () => {
            document.querySelectorAll(".menu-filter").forEach(item => item.classList.remove("active"));
            button.classList.add("active");

            const filter = button.dataset.filter;
            document.querySelectorAll(".menu-card").forEach(card => {
                const category = card.dataset.category || "";
                const visible = filter === "all" || category.includes(filter);
                card.classList.toggle("filtered-out", !visible);
            });
        });
    });

    const lightbox = document.getElementById("lightbox");
    const lightboxImage = document.getElementById("lightboxImage");
    const lightboxClose = document.getElementById("lightboxClose");

    const closeLightbox = () => {
        lightbox?.classList.remove("open");
        lightbox?.setAttribute("aria-hidden", "true");
        body.style.overflow = "";
    };

    document.querySelectorAll("[data-lightbox]").forEach(item => {
        item.addEventListener("click", () => {
            if (!lightbox || !lightboxImage) return;
            lightboxImage.src = item.dataset.lightbox;
            lightbox.classList.add("open");
            lightbox.setAttribute("aria-hidden", "false");
            body.style.overflow = "hidden";
        });
    });

    lightboxClose?.addEventListener("click", closeLightbox);
    lightbox?.addEventListener("click", event => {
        if (event.target === lightbox) closeLightbox();
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") closeLightbox();
    });

    const dateInput = document.querySelector('input[type="date"][name="date"]');
    if (dateInput) {
        dateInput.min = new Date().toISOString().split("T")[0];
    }

    backToTop?.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    const year = document.getElementById("currentYear");
    if (year) year.textContent = new Date().getFullYear();

    const currentPath = window.location.pathname.replace(/\/+$/, "") || "/";
    mainNav?.querySelectorAll("a").forEach(link => {
        const linkPath = new URL(link.href).pathname.replace(/\/+$/, "") || "/";
        link.classList.toggle("active", linkPath === currentPath);
    });
})();
