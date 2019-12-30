# Team
This actor will return a list of team members information (as a json string), with the format described at [data_team](https://github.com/threefoldfoundation/data_team) repository, it also enabled filtering them by [project](https://github.com/threefoldfoundation/data_team#project-ids) or [contribution type](https://github.com/threefoldfoundation/data_team#contribution-ids).


## list_memebrs(projects, contribution_types)
List all memebrs filtered by projects and contribution types.

Accepts:
- `projects`: an optional list of [project ids](https://github.com/threefoldfoundation/data_team#project-ids) to filter by
- `contribution_types`: an optional list of [contribution ids](https://github.com/threefoldfoundation/data_team#contribution-ids) to filter by (can be empty).

## Examples

```
JSX> cl.actors.team.list_members([1], [1])
b'[{"avatar": "olivia_jurado/olivia_jurado_processed.jpg", "full_name": "Olivia Jurado", "description": "Olivia is a Co-Founder of the THREEFOLD LOVE
 initiative, with a mission of digital inclusion by empowering communities through the use of ThreeFold technologies. \xc2\xa0\\n\\nOlivia is an eco-
socialpreneur and serial volunteer. Living each day in mindful ways in an attempt to get back to a manner of living that is more harmonious with natu
...
```
