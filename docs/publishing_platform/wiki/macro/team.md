# Team

This macro can be used to generate the data required for our [docify plugin](https://github.com/threefoldtech/jumpscale_weblibs/tree/master/static/team) for listing of team members.

### Syntax:

```
!!!team("link_to_data_team_repo")
```

or using toml (inside a code block)

````
```
!!!team
link = "data_team_repo"
```
````

The **link** can be in the format of our [custom links](../links.md).

`link` is the link to data directory at the data repository it should follow the same format described [here](https://github.com/threefoldfoundation/data_team)(also the list of project ids and contribution types).


### Other options
* `order`: the order of team members listing, either `rank` or `random`.
* `projects`: a list of project ids to filter by
* `contribution_types`: a list of contribution ids to filter by


### Examples

#### List all team members

```
!!!team("https://github.com/threefoldfoundation/data_team/tree/master/team")
```

#### List all members ordered by rank

```
!!!team("https://github.com/threefoldfoundation/data_team/tree/master/team", order="rank")
```

#### List all members of project ThreeFold Tech and order them by rank

````
```
!!!team
link = "https://github.com/threefoldfoundation/data_team/tree/master/team"
order = "rank"
projects = [2]
```
````

#### List all contributors of codescalers

````
```
!!!team
link = "https://github.com/threefoldfoundation/data_team/tree/master/team"
order = "random"
projects = [8]
contribution_types = [3]
```
````
