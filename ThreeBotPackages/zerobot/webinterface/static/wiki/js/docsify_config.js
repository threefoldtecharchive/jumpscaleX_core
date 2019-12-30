
mermaid.initialize({ startOnLoad: false });

function docsifyConfig(name, repo) {
    basePath = location.protocol + "//" + location.hostname + "/3git/wikis/" + name;
    imagesPath = location.protocol + "//" + location.hostname + "/3git/wikis/";
    TeamWidget.avatarPrefix = basePath;

    window.$docsify = {
        coverpage: false,
        homepage: 'readme.md',
        basePath: basePath,
        name: 'ThreeFold Foundation ' + name.charAt(0).toUpperCase() + name.slice(1),
        el: '#main_wiki_container',
        disqus: '//tf-foundation.disqus.com/embed.js',
        repo: repo || ('https://github.com/threefoldfoundation/' + name),
        loadSidebar: true,
        executeScript: true,
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

                        let rendered_code = function (code) {
                            code = code.replaceAll("$path", imagesPath);
                            return code;
                        }
                        let images_counter = findAll("<img", rendered_code(code)).length
                        if (images_counter < 2) {
                            return (`<div class="slides" style="position: initial;">${rendered_code(code)}</div>`)
                        }
                        return (`<div class="reveal"><div class="slides" style="position: initial;">${rendered_code(code)}</div></div>`);
                    }
                    if (lang === "gallery") {
                        return (`<div class="gallery" style="position: initial;">${code}</div>`);
                    }
                    if (lang === "team") {
                        var data = JSON.parse(code);
                        return TeamWidget.render(data.dataset, data.order);
                    }
                    if (lang === "markdown") {
                        return (`<div class="reveal"><div class="slides" style="position: initial;">${code}</div></div>`);
                    }
                    if (lang === "inline_html") {
                        return `${code}`;
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
// helper methods
// replace all in a string
String.prototype.replaceAll = function (stringToFind, stringToReplace) {
    if (stringToFind === stringToReplace) return this;
    var temp = this;
    var index = temp.indexOf(stringToFind);
    while (index != -1) {
        temp = temp.replace(stringToFind, stringToReplace);
        index = temp.indexOf(stringToFind);
    }
    return temp;
};
// find all matches
function findAll(regexPattern, sourceString) {
    let output = []
    let match
    let regexPatternWithGlobal = RegExp(regexPattern, "g")
    while (match = regexPatternWithGlobal.exec(sourceString)) {
        delete match.input
        output.push(match)
    }
    return output
}
