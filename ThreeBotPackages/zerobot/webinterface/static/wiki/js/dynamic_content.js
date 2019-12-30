function callActorAndRender(package, actor, method, args, containerId, isMarkdown) {
    let threebotName, packageName;
    [threebotName, packageName] = package.split(".");
    packageGedisClient[threebotName][packageName].actors[actor][method](args).then(response => {
        response.json().then(data => {
            let container = $(`#container_${containerId}`);
            let spinner = $(`#spinner_${containerId}`);
            let content = data.content;
            if (isMarkdown) {
                content = marked(content);
            }
            container.append(content);
            spinner.hide();
        });
    });
}
