from Jumpscale import j
from JumpscaleLibs.tools.markdowndocs.Link import MarkdownLinkParser


def filter_on(data, attr, values):
    values = set(values)

    def filter_by_attr(person):
        try:
            return any([value in person[attr] for value in values])
        except KeyError:
            return False

    return list(filter(filter_by_attr, data))


def filter_on_mapping(mapping, data):
    """filter on mapping of projects and contribution types

    :param mapping: list of tuples (project_id, contribution_id) e.g. [(1, 1), (1,2)]
    :type mapping: [tuple]
    :param data: team data
    :type data: [dict]
    """
    new_data = []

    for person in data:
        projects, contributions = person["project_ids"], person["contribution_ids"]
        for item in zip(projects, contributions):
            if item in mapping:
                new_data.append(person)
                break

    return new_data


def team(doc, link, order="random", projects=None, contribution_types=None, pull=False, **kwargs):
    """generate the json requried for docify team plugin
       for the full list of project ids, contribution types, also the toml data see
       https://github.com/threefoldfoundation/data_team/tree/master/README.md

    :param doc: current doc
    :type doc: Doc
    :param link: a link to team data repository, e.g. https://github.com/threefoldfoundation/data_team/tree/master/team
    :type link: str
    :param order: listing order, either 'random' or 'rank', defaults to 'random'
    :type order: str, optional
    :param projects: project ids to filter by, defaults to None, will include all projects
    :type projects: [int], optional
    :param contribution_types: contribution types to filter by
    :type contribution_types: [int], optional
    :return: a codeblock content with type `team`
    :rtype: str
    """

    repo = doc.docsite.get_real_source(MarkdownLinkParser(link))
    path = j.clients.git.getContentPathFromURLorPath(repo, pull=pull)

    # options passed to team plugin (docsify)
    options = {"order": order}

    data = []
    for directory in j.sal.fs.listDirsInDir(path):
        person_data = {}

        for filepath in j.sal.fs.listFilesInDir(directory):
            basename = j.sal.fs.getBaseName(filepath).lower()
            extname = j.sal.fs.getFileExtension(filepath)
            if basename.startswith("publicinfo") and extname == "toml":
                person_data.update(j.data.serializers.toml.load(filepath))
            elif extname in ("png", "jpg", "jpeg"):
                person_data["avatar"] = j.sal.fs.joinPaths(doc.path_dir_rel, basename)
                dest = j.sal.fs.joinPaths(doc.docsite.outpath, doc.path_dir_rel, basename)
                j.sal.fs.copyFile(filepath, dest, createDirIfNeeded=True)

        if person_data:
            data.append(person_data)

    if projects:
        data = filter_on(data, "project_ids", projects)
    if contribution_types:
        data = filter_on(data, "contribution_ids", contribution_types)
        if projects and len(projects) == len(contribution_types):
            # ensure the order of filtration is respected
            # mapping for example projects of [1,2] to contributions types of [1,4]
            # so will show 1:1 (project:contribution_type) and 2:4
            mapping = list(zip(projects, contribution_types))
            data = filter_on_mapping(mapping, data)

    options["dataset"] = data
    return "```team\n%s\n```" % j.data.serializers.json.dumps(options)
