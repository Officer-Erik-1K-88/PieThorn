(function () {
    function getContentRoot() {
        var html = document.documentElement;
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

    function normalizePathname(pathname) {
        return pathname.endsWith("/") ? pathname : pathname + "/";
    }

    function detectCurrentVersion(versions, siteRoot) {
        var pathname = normalizePathname(window.location.pathname);

        for (var i = 0; i < versions.length; i += 1) {
            var versionPath = normalizePathname(new URL(versions[i].path, siteRoot).pathname);
            if (pathname === versionPath || pathname.indexOf(versionPath) === 0) {
                return versions[i];
            }
        }

        return null;
    }

    function buildTargetUrl(siteRoot, currentVersionRoot, nextVersion) {
        var currentPage = new URL(window.location.href);
        var relativePath = currentPage.pathname.slice(currentVersionRoot.pathname.length);
        var targetRoot = new URL(nextVersion.path, siteRoot);
        var targetPath = relativePath || "index.html";
        var targetUrl = new URL(targetPath, targetRoot);

        targetUrl.hash = currentPage.hash;
        targetUrl.search = currentPage.search;
        return targetUrl;
    }

    async function initVersionSwitcher() {
        var container = document.getElementById("version-switcher");
        var select = document.getElementById("version-select");
        var currentVersionRoot = getVersionRoot();

        if (!container || !select || !currentVersionRoot) {
            return;
        }

        var versionsUrl = new URL("../versions.json", currentVersionRoot);
        var response = await fetch(versionsUrl);
        if (!response.ok) {
            return;
        }

        var payload = await response.json();
        var siteRoot = new URL("./", versionsUrl);
        var versions = Array.isArray(payload.versions) ? payload.versions : [];
        if (versions.length < 2) {
            return;
        }

        var currentVersion = detectCurrentVersion(versions, siteRoot);

        versions.forEach(function (version) {
            var option = document.createElement("option");
            option.value = version.name;
            option.textContent = version.name === payload.latest ? version.name + " (latest)" : version.name;
            if (currentVersion && currentVersion.name === version.name) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        select.addEventListener("change", function (event) {
            var nextVersion = versions.find(function (version) {
                return version.name === event.target.value;
            });

            if (!nextVersion) {
                return;
            }

            var targetUrl = buildTargetUrl(siteRoot, currentVersionRoot, nextVersion);
            window.location.assign(targetUrl.toString());
        });

        container.hidden = false;
    }

    function start() {
        initVersionSwitcher().catch(function () {
            /* Ignore version switcher failures so the docs still render. */
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
}());
