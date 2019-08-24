
mermaid.initialize({ startOnLoad: false });

function docsifyConfig(name, repo) {
    basePath = location.protocol + "//" + location.hostname + ":4442/docsites/" + name;
    TeamWidget.avatarPrefix = basePath;

    window.$docsify = {
        coverpage: false,
        homepage: 'readme.md',
        basePath: basePath,
        name: 'ThreeFold Foundation ' + name.charAt(0).toUpperCase() + name.slice(1),
        el: '#app_' + name,
        disqus: '//tf-foundation.disqus.com/embed.js',
        repo: repo || ('https://github.com/threefoldfoundation/' + name),
        loadSidebar: true,
        markdown: {
            renderer: {
                code: function (code, lang) {
                    if (lang === "mermaid") {
                        return ('<div class="mermaid">' + mermaid.render(lang, code) + "</div>");
                    }
                    if (lang === "gslide") {
                        return (`<div class="reveal"><div class="slides" style="position: initial;">${code}</div></div>`);
                    }
                    if (lang === "slideshow") {
                        return (`<div class="reveal"><div class="slides" style="position: initial;">${code}</div></div>`);
                    }
                    if (lang === "gallery") {
                        return (`<div class="gallery" style="position: initial;">${code}</div>`);
                    }
                    if (lang === "team") {
                        var data = JSON.parse(code);
                        return TeamWidget.render(data.dataset, data.order);
                    }
                    return this.origin.code.apply(this, arguments);
                }
            }
        },
        search: {
            maxAge: 86400000, // Expiration time, the default one day
            placeholder: 'Type to search',
            noData: 'No Results!',
            name: name,

            // Headline depth, 1 - 6
            depth: 2,

            hideOtherSidebarContent: false, // whether or not to hide other sidebar content
        },
        plugins: [
            function (hook) {
                hook.doneEach(() => {
                    var url = new URL(window.location.href.replace('#', ''));
                    var params = new URLSearchParams(url.search)

                    // sidebar
                    var sidebar = params.get('sidebar');
                    const dom = document.querySelector('body');
                    if (sidebar == 'hide') {
                        dom.classList.add('no-sidebar');
                    } else if (sidebar == "collapse") {
                        dom.classList.add('close');
                    }

                    // github logo
                    var github = params.get('github')
                    if (github === 'hide') {
                        document.querySelector('.github-corner').hidden = true;
                    }
                });
            },

            TeamWidgetPlugin(),

            function (hook) {
                hook.doneEach(() => {
                    // gallery
                    // do not init gallery if not loaded into dom
                    if (!document.querySelector('.gallery')) {
                        return;
                    }
                    $('.gallery a').simpleLightbox();
                });
            },

            function (hook) {
                hook.doneEach(() => {
                    // do not init reveal if no slides are loaded into dom
                    if (!document.querySelector('.reveal .slides')) {
                        return;
                    }
                    Reveal.initialize({ showNotes: true });
                });
            },
        ]
    };
}
