(function () {
    function getVersionRoot() {
        if (!window.DOCUMENTATION_OPTIONS || !window.DOCUMENTATION_OPTIONS.URL_ROOT) {
            return null;
        }

        return new URL(window.DOCUMENTATION_OPTIONS.URL_ROOT, window.location.href);
    }

    function detectVersionLabel() {
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

    function buildNav(siteRoot, versionLabel) {
        var nav = document.createElement("nav");
        nav.className = "site-top-nav";
        nav.setAttribute("aria-label", "Site");

        var latestHref = new URL("docs/latest/index.html", siteRoot);
        var docsHref = new URL("docs/", siteRoot);

        nav.innerHTML =
            '<div class="site-top-nav__inner">' +
            '<div class="site-top-nav__brand">PieThorn</div>' +
            '<div class="site-top-nav__links">' +
            '<a href="' + siteRoot.toString() + '">Home</a>' +
            '<a href="' + docsHref.toString() + '">Docs</a>' +
            '<a href="' + latestHref.toString() + '">Latest Docs</a>' +
            '</div>' +
            (versionLabel ? '<div class="site-top-nav__meta">Viewing ' + versionLabel + '</div>' : "") +
            "</div>";

        return nav;
    }

    function initTopNav() {
        if (!document.body || document.querySelector(".site-top-nav")) {
            return;
        }

        var currentVersionRoot = getVersionRoot();
        if (!currentVersionRoot) {
            return;
        }

        var siteRoot = new URL("../../", currentVersionRoot);
        var nav = buildNav(siteRoot, detectVersionLabel());
        document.body.insertBefore(nav, document.body.firstChild);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initTopNav);
    } else {
        initTopNav();
    }
}());
