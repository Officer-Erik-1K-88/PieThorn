import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { JSDOM } from "jsdom";

function fail(message) {
    throw new Error(message);
}

function fileUrlFor(rootDir, relativePath) {
    return pathToFileURL(path.join(rootDir, relativePath)).toString();
}

async function readText(rootDir, relativePath) {
    return fs.readFile(path.join(rootDir, relativePath), "utf8");
}

async function main() {
    const siteRoot = process.argv[2];
    if (!siteRoot) {
        fail("Usage: node scripts/test_docs_ui.mjs <site-dir>");
    }

    const versionsPayload = JSON.parse(await readText(siteRoot, "docs/versions.json"));
    const latestVersion = versionsPayload.latest;
    if (!latestVersion) {
        fail("docs/versions.json does not define a latest version");
    }

    async function runPage(relativePath, pageUrl, mode) {
        const html = await readText(siteRoot, relativePath);
        const dom = new JSDOM(html, {
            url: pageUrl,
            runScripts: "outside-only",
            pretendToBeVisual: true,
        });

        const { window } = dom;
        const errors = [];
        window.console.error = (...args) => errors.push(args.map(String).join(" "));

        if (mode === "hosted") {
            window.fetch = async (resource) => {
                const requestUrl = typeof resource === "string" ? resource : resource.toString();
                const url = new URL(requestUrl, pageUrl);
                const prefix = "/PieThorn/";
                if (!url.pathname.startsWith(prefix)) {
                    throw new Error(`Unexpected fetch path: ${url.pathname}`);
                }

                const fetchedPath = url.pathname.slice(prefix.length);
                const body = await readText(siteRoot, fetchedPath);
                return {
                    ok: true,
                    async json() {
                        return JSON.parse(body);
                    },
                };
            };
        } else {
            window.fetch = async () => {
                throw new Error("fetch should not be needed for file previews");
            };
        }

        const scripts = [
            path.join("docs", latestVersion, "_static", "documentation_options.js"),
            path.join("docs", latestVersion, "_static", "top-nav.js"),
            path.join("docs", latestVersion, "_static", "version-switcher.js"),
        ];

        for (const scriptPath of scripts) {
            const code = await readText(siteRoot, scriptPath);
            window.eval(code);
        }

        if (window.document.readyState === "loading") {
            window.document.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true }));
        }

        await new Promise((resolve) => setTimeout(resolve, 50));
        return { window, errors };
    }

    const hostedDocsPath = path.join("docs", latestVersion, "index.html");
    const hosted = await runPage(hostedDocsPath, `https://example.test/PieThorn/${hostedDocsPath}`, "hosted");
    const hostedNav = hosted.window.document.querySelector(".site-top-nav");
    const hostedSwitcher = hosted.window.document.getElementById("version-switcher");
    const hostedOptions = [...hosted.window.document.querySelectorAll("#version-select option")];

    if (!hostedNav) {
        fail(`Hosted docs top nav was not rendered. Console errors: ${hosted.errors.join(" | ") || "none"}`);
    }
    if (!hostedSwitcher || hostedSwitcher.hidden) {
        fail(`Hosted version switcher did not render. Console errors: ${hosted.errors.join(" | ") || "none"}`);
    }
    if (hostedOptions.length < 2) {
        fail(`Expected at least 2 hosted version options, found ${hostedOptions.length}`);
    }

    const fileRoot = path.resolve(siteRoot);
    const fileHome = await runPage("index.html", fileUrlFor(fileRoot, "index.html"), "file");
    const fileHomeNav = fileHome.window.document.querySelector(".site-top-nav");
    if (!fileHomeNav) {
        fail(`Local file homepage top nav was not rendered. Console errors: ${fileHome.errors.join(" | ") || "none"}`);
    }

    const fileDocs = await runPage(hostedDocsPath, fileUrlFor(fileRoot, hostedDocsPath), "file");
    const fileDocsNav = fileDocs.window.document.querySelector(".site-top-nav");
    const fileDocsSwitcher = fileDocs.window.document.getElementById("version-switcher");
    const fileOptions = [...fileDocs.window.document.querySelectorAll("#version-select option")];

    if (!fileDocsNav) {
        fail(`Local file docs top nav was not rendered. Console errors: ${fileDocs.errors.join(" | ") || "none"}`);
    }
    if (!fileDocsSwitcher || fileDocsSwitcher.hidden) {
        fail(`Local file docs version switcher did not render. Console errors: ${fileDocs.errors.join(" | ") || "none"}`);
    }
    if (fileOptions.length < 2) {
        fail(`Expected at least 2 local file version options, found ${fileOptions.length}`);
    }

    console.log(
        JSON.stringify(
            {
                latestVersion,
                hostedNavText: hostedNav.textContent.replace(/\s+/g, " ").trim(),
                fileHomeNavText: fileHomeNav.textContent.replace(/\s+/g, " ").trim(),
                fileDocsNavText: fileDocsNav.textContent.replace(/\s+/g, " ").trim(),
                versions: fileOptions.map((option) => option.textContent),
            },
            null,
            2,
        ),
    );
}

main().catch((error) => {
    console.error(error.stack || String(error));
    process.exitCode = 1;
});
