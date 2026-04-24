(function () {
    function normalizeSitePath(path) {
        if (!path) {
            return "index.html";
        }

        var normalized = path.replace(/^\/+/, "");
        if (!normalized) {
            return "index.html";
        }

        return normalized.endsWith("/") ? normalized + "index.html" : normalized;
    }

    function getContentRoot() {
        var html = document.documentElement;
        if (html) {
            var contentRoot = html.getAttribute("data-content_root");
            if (contentRoot) {
                return contentRoot;
            }
        }

        if (html && html.dataset && html.dataset.contentRoot) {
            return html.dataset.contentRoot;
        }

        if (
            window.DOCUMENTATION_OPTIONS &&
            typeof window.DOCUMENTATION_OPTIONS.URL_ROOT === "string" &&
            window.DOCUMENTATION_OPTIONS.URL_ROOT
        ) {
            return window.DOCUMENTATION_OPTIONS.URL_ROOT;
        }

        return null;
    }

    function getVersionRoot() {
        var contentRoot = getContentRoot();
        if (!contentRoot) {
            return null;
        }

        return new URL(contentRoot, window.location.href);
    }

    function getEmbeddedPayload(scriptId) {
        var script = document.getElementById(scriptId);
        if (!script || !script.textContent) {
            return null;
        }

        try {
            return JSON.parse(script.textContent);
        } catch (error) {
            return null;
        }
    }

    function detectVersionLabel(currentVersionRoot) {
        if (currentVersionRoot) {
            var trimmed = currentVersionRoot.pathname.replace(/\/+$/, "");
            var pieces = trimmed.split("/").filter(Boolean);
            if (pieces.length) {
                return pieces[pieces.length - 1];
            }
        }

        var marker = "/docs/";
        var pathname = window.location.pathname;
        var index = pathname.indexOf(marker);
        if (index === -1) {
            return null;
        }

        var remainder = pathname.slice(index + marker.length);
        var version = remainder.split("/")[0];
        return version || null;
    }

    function resolveSiteContext() {
        var existingNav = document.querySelector(".site-top-nav");
        if (existingNav && existingNav.dataset.siteRootPrefix !== undefined) {
            return {
                nav: existingNav,
                siteRoot: new URL(existingNav.dataset.siteRootPrefix || "./", window.location.href),
                currentPath: normalizeSitePath(existingNav.dataset.currentPath),
                currentLabel: existingNav.dataset.currentLabel || null,
            };
        }

        var currentVersionRoot = getVersionRoot();
        if (!currentVersionRoot) {
            return null;
        }

        var siteRoot = new URL("../../", currentVersionRoot);
        var relativePath = normalizeSitePath(window.location.pathname.slice(siteRoot.pathname.length));
        return {
            nav: null,
            siteRoot: siteRoot,
            currentPath: relativePath,
            currentLabel: detectVersionLabel(currentVersionRoot),
        };
    }

    function isActiveLink(currentPath, targetPath) {
        var normalizedCurrent = normalizeSitePath(currentPath);
        var normalizedTarget = normalizeSitePath(targetPath);

        if (normalizedTarget === "docs/index.html") {
            return normalizedCurrent === "docs/index.html" || normalizedCurrent.indexOf("docs/") === 0;
        }

        if (normalizedTarget === "docs/latest/index.html") {
            return normalizedCurrent === normalizedTarget;
        }

        return normalizedCurrent === normalizedTarget;
    }

    function buildLink(siteRoot, currentPath, entry) {
        var link = document.createElement("a");
        link.href = new URL(entry.path, siteRoot).toString();
        link.textContent = entry.label;

        if (isActiveLink(currentPath, entry.path)) {
            link.setAttribute("aria-current", "page");
        }

        return link;
    }

    function buildNavElement(siteRoot, currentPath, currentLabel, payload) {
        var nav = document.createElement("nav");
        nav.className = "site-top-nav";
        nav.setAttribute("aria-label", "Site");

        var inner = document.createElement("div");
        inner.className = "site-top-nav__inner";
        nav.appendChild(inner);

        var brand = document.createElement("div");
        brand.className = "site-top-nav__brand";
        brand.textContent = "PieThorn";
        inner.appendChild(brand);

        var links = document.createElement("div");
        links.className = "site-top-nav__links";
        inner.appendChild(links);

        var pageEntries = Array.isArray(payload.pages) ? payload.pages : [];
        pageEntries.forEach(function (entry) {
            if (!entry || !entry.label || !entry.path) {
                return;
            }
            links.appendChild(buildLink(siteRoot, currentPath, entry));
        });

        var docs = payload.docs || {};
        var docsEntries = [
            { label: "Docs", path: docs.home || "docs/" },
            { label: "Latest Docs", path: docs.latest || "docs/latest/index.html" },
        ];

        docsEntries.forEach(function (entry) {
            links.appendChild(buildLink(siteRoot, currentPath, entry));
        });

        if (currentLabel) {
            var meta = document.createElement("div");
            meta.className = "site-top-nav__meta";
            meta.textContent = "Viewing " + currentLabel;
            inner.appendChild(meta);
        }

        return nav;
    }

    async function loadNavPayload(siteRoot) {
        var embeddedPayload = getEmbeddedPayload("site-nav-data");
        if (embeddedPayload) {
            return embeddedPayload;
        }

        var response = await fetch(new URL("site-nav.json", siteRoot));
        if (!response.ok) {
            throw new Error("Failed to load site-nav.json");
        }
        return response.json();
    }

    async function initTopNav() {
        if (!document.body) {
            return;
        }

        var context = resolveSiteContext();
        if (!context) {
            return;
        }

        var payload = await loadNavPayload(context.siteRoot);
        var nav = buildNavElement(context.siteRoot, context.currentPath, context.currentLabel, payload);

        if (context.nav) {
            context.nav.replaceWith(nav);
        } else if (!document.querySelector(".site-top-nav")) {
            document.body.insertBefore(nav, document.body.firstChild);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            initTopNav().catch(function () {
                /* Ignore nav failures so the page still renders. */
            });
        });
    } else {
        initTopNav().catch(function () {
            /* Ignore nav failures so the page still renders. */
        });
    }
}());
